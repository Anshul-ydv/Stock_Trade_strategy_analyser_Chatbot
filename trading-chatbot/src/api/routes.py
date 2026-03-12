import csv
from datetime import date, timedelta
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import get_settings
from ..data.fetchers import fetch_ohlcv
from ..ta_engine import (
    compute_indicators,
    detect_breakout,
    detect_double_top_bottom,
    detect_vcp,
    detect_sma_crossover,
    detect_macd_cross,
)
from ..fa_engine import evaluate_fundamentals
from ..strategy_engine import rank_strategies
from ..chat_agent import ChatAgent
from ..llm_client import LLMClient
from ..utils import get_logger, read_tickers
from ..data.news_fetcher import fetch_news

logger = get_logger(__name__)
router = APIRouter()

# Cache the ChatAgent as a module-level singleton to avoid
# re-bootstrapping the RAG index and embedding model on every request.
_chat_agent: ChatAgent | None = None


def _get_chat_agent() -> ChatAgent:
    """Return a cached ChatAgent singleton."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent


# ── Pydantic models ────────────────────────────────────────────────

class StrategyResponse(BaseModel):
    ticker: str
    strategy: str
    score: float
    entry: float
    stop: float
    target: float
    reasons: List[str]

class ChatRequest(BaseModel):
    ticker: str
    strategy: Optional[str] = None
    question: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class AddTickerRequest(BaseModel):
    ticker: str

class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    support: Optional[float] = None
    resistance: Optional[float] = None


class FundamentalResponse(BaseModel):
    ticker: str
    metrics: Dict[str, Any]
    score: float
    strengths: List[str]
    risks: List[str]

class SentimentResponse(BaseModel):
    ticker: str
    score: str
    summary: str
    news: List[Dict[str, str]]

# ── Ticker management routes ───────────────────────────────────────

@router.post("/tickers")
async def add_ticker(request: AddTickerRequest):
    """Add a new ticker to the watchlist CSV."""
    ticker = request.ticker.upper().strip()
    settings = get_settings()
    csv_path = settings.tickers_file

    existing = read_tickers()
    if ticker in existing:
        return {"message": f"{ticker} already exists"}

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ticker, "NSE"])

    return {"message": f"Added {ticker}"}


@router.delete("/tickers/{ticker}")
async def remove_ticker(ticker: str):
    """Remove a ticker from the watchlist CSV."""
    ticker = ticker.upper().strip()
    settings = get_settings()
    csv_path = settings.tickers_file

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Ticker file not found")

    rows = []
    found = False
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["ticker"].strip().upper() == ticker:
                found = True
                continue
            rows.append(row)

    if not found:
        raise HTTPException(status_code=404, detail="Ticker not found")

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {"message": f"Removed {ticker}"}


# ── Fundamentals route ─────────────────────────────────────────────

@router.get("/fundamentals/{ticker}", response_model=FundamentalResponse)
async def get_fundamentals(ticker: str):
    """Return key fundamental metrics for a given ticker."""
    try:
        fundamentals = evaluate_fundamentals(ticker)
        return FundamentalResponse(
            ticker=fundamentals.ticker,
            metrics=fundamentals.metrics,
            score=fundamentals.score,
            strengths=fundamentals.strengths,
            risks=fundamentals.risks
        )
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fundamentals")

# ── Sentiment route ────────────────────────────────────────────────

@router.get("/sentiment/{ticker}", response_model=SentimentResponse)
async def get_sentiment(ticker: str):
    """Fetch recent news and summarize sentiment via LLM."""
    news_items = fetch_news(ticker, limit=5)
    if not news_items:
        return SentimentResponse(
            ticker=ticker,
            score="Neutral",
            summary=f"No recent news found for {ticker} to analyze.",
            news=[]
        )
    
    # Prompt the LLM
    news_text = "\n".join([f"- {n['title']}" for n in news_items])
    prompt = f"""Analyze the sentiment of the following recent news headlines for {ticker}.
    
    News:
    {news_text}
    
    CRITICAL STRUCTURE REQUIREMENT:
    Return exactly two lines as follows, with no intro or outro text:
    SCORE: [Bullish, Bearish, or Neutral]
    SUMMARY: [A 2-sentence summary of the news]
    """
    
    llm = LLMClient()
    response = llm.generate(prompt)
    
    score = "Neutral"
    summary_text = "Analysis unavailable."
    
    if response and response.text:
        lines = response.text.split("\n")
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SCORE:"):
                score = line.split(":", 1)[1].strip()
            elif line.upper().startswith("SUMMARY:"):
                summary_text = line.split(":", 1)[1].strip()
        
        # Clean up score if LLM adds punctuation
        score = score.strip("*. \t\n")
        if "bullish" in score.lower(): score = "Bullish"
        elif "bearish" in score.lower(): score = "Bearish"
        else: score = "Neutral"
    
    return SentimentResponse(
        ticker=ticker,
        score=score.title(),
        summary=summary_text,
        news=news_items
    )

# ── Chart history route ────────────────────────────────────────────

@router.get("/history/{ticker}", response_model=List[Candle])
async def get_history(ticker: str, days: int = 180):
    """Return OHLCV candle data with technical overlays for charting."""
    start = date.today() - timedelta(days=days)
    df = fetch_ohlcv(ticker, start=start)

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    enriched = compute_indicators(df)

    candles = []
    for idx, row in enriched.iterrows():
        candles.append(Candle(
            time=idx.strftime("%Y-%m-%d"),
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=int(row['volume']),
            ema_9=row.get('ema_9'),
            ema_21=row.get('ema_21'),
            support=row.get('support'),
            resistance=row.get('resistance')
        ))
    return candles


# ── Stock screening route ──────────────────────────────────────────

@router.get("/screen", response_model=List[StrategyResponse])
async def screen_stocks(
    strategy: Optional[str] = None,
    limit: int = 10,
    lookback_days: int = 180
):
    """Screen tickers and return ranked strategy results."""
    tickers = read_tickers(limit=limit)
    results = []

    start = date.today() - timedelta(days=lookback_days)

    for ticker in tickers:
        try:
            df = fetch_ohlcv(ticker, start=start)
            if df is None or df.empty:
                continue

            enriched = compute_indicators(df)
            signals = []
            for detector in [
                detect_breakout,
                detect_double_top_bottom,
                detect_vcp,
                detect_sma_crossover,
                detect_macd_cross,
            ]:
                sig = detector(ticker, enriched)
                if sig:
                    signals.append(sig)

            fundamentals = evaluate_fundamentals(ticker)
            strategies = rank_strategies(ticker, enriched, fundamentals, signals=signals)

            for s in strategies:
                if strategy and s.strategy.lower() != strategy.lower():
                    continue

                results.append(StrategyResponse(
                    ticker=ticker,
                    strategy=s.strategy,
                    score=s.score,
                    entry=s.entry,
                    stop=s.stop,
                    target=s.target,
                    reasons=s.reasons
                ))
        except Exception as e:
            logger.error("Error processing %s: %s", ticker, e)
            continue

    return sorted(results, key=lambda x: x.score, reverse=True)


# ── Chat route ─────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle a chat query using the cached ChatAgent."""
    try:
        agent = _get_chat_agent()

        start = date.today() - timedelta(days=180)
        df = fetch_ohlcv(request.ticker, start=start)

        if df is None or df.empty:
            return ChatResponse(
                response=f"I couldn't retrieve data for {request.ticker}. "
                "Please check the ticker symbol or try again later."
            )

        enriched = compute_indicators(df)
        fundamentals = evaluate_fundamentals(request.ticker)

        strategies = rank_strategies(request.ticker, enriched, fundamentals)

        if not strategies:
            return ChatResponse(
                response=f"I analyzed {request.ticker} but couldn't find "
                "a clear trading strategy at this moment."
            )

        chosen_strategy = next(
            (s for s in strategies if s.strategy == request.strategy),
            strategies[0],
        )

        response_text = agent.explain(
            request.ticker,
            chosen_strategy,
            fundamentals,
            user_question=request.question,
        )

        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error("Chat error for %s: %s", request.ticker, e)
        return ChatResponse(
            response=f"I encountered an error analyzing {request.ticker}. Please try again."
        )

-- CreateTable
CREATE TABLE "PipelineRun" (
    "id" TEXT NOT NULL,
    "runDate" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "sectorsTargeted" TEXT[],
    "totalStocksAnalyzed" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PipelineRun_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Recommendation" (
    "id" TEXT NOT NULL,
    "runId" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "finalScore" DOUBLE PRECISION NOT NULL,
    "verdict" TEXT NOT NULL,
    "entryLow" DOUBLE PRECISION NOT NULL,
    "entryHigh" DOUBLE PRECISION NOT NULL,
    "stopLoss" DOUBLE PRECISION NOT NULL,
    "target" DOUBLE PRECISION NOT NULL,
    "rrRatio" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Recommendation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ScoreBreakdown" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "techScore" DOUBLE PRECISION NOT NULL,
    "fundScore" DOUBLE PRECISION NOT NULL,
    "sectorScore" DOUBLE PRECISION NOT NULL,
    "sentimentScore" DOUBLE PRECISION NOT NULL,
    "riskPenalty" DOUBLE PRECISION NOT NULL,
    "finalScore" DOUBLE PRECISION NOT NULL,

    CONSTRAINT "ScoreBreakdown_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TechnicalSignal" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "date" TIMESTAMP(3) NOT NULL,
    "ema20" DOUBLE PRECISION NOT NULL,
    "ema50" DOUBLE PRECISION NOT NULL,
    "ema200" DOUBLE PRECISION NOT NULL,
    "macdLine" DOUBLE PRECISION NOT NULL,
    "macdSignal" DOUBLE PRECISION NOT NULL,
    "macdHistogram" DOUBLE PRECISION NOT NULL,
    "rsi" DOUBLE PRECISION NOT NULL,
    "bbUpper" DOUBLE PRECISION NOT NULL,
    "bbLower" DOUBLE PRECISION NOT NULL,
    "atr" DOUBLE PRECISION NOT NULL,
    "volumeSpike" BOOLEAN NOT NULL,
    "obvTrend" TEXT NOT NULL,

    CONSTRAINT "TechnicalSignal_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "FundamentalData" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "peRatio" DOUBLE PRECISION,
    "pegRatio" DOUBLE PRECISION,
    "roe" DOUBLE PRECISION,
    "roa" DOUBLE PRECISION,
    "debtToEquity" DOUBLE PRECISION,
    "interestCoverage" DOUBLE PRECISION,
    "revenueGrowth" DOUBLE PRECISION,
    "epsGrowth" DOUBLE PRECISION,
    "freeCashFlow" DOUBLE PRECISION,

    CONSTRAINT "FundamentalData_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SentimentData" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "newsScore" DOUBLE PRECISION NOT NULL,
    "insiderSignal" TEXT NOT NULL,
    "earningsSurprise" DOUBLE PRECISION,
    "headlinesJson" JSONB NOT NULL,

    CONSTRAINT "SentimentData_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "LlmOutput" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "stage" INTEGER NOT NULL,
    "promptHash" TEXT NOT NULL,
    "responseJson" JSONB NOT NULL,
    "tokensUsed" INTEGER NOT NULL,
    "latencyMs" INTEGER NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "LlmOutput_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BacktestResult" (
    "id" TEXT NOT NULL,
    "ticker" TEXT NOT NULL,
    "signalDate" TIMESTAMP(3) NOT NULL,
    "entryPrice" DOUBLE PRECISION NOT NULL,
    "exitPrice" DOUBLE PRECISION,
    "exitDate" TIMESTAMP(3),
    "returnPct" DOUBLE PRECISION,
    "hitTarget" BOOLEAN NOT NULL DEFAULT false,
    "hitStop" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BacktestResult_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "ScoreBreakdown_recommendationId_key" ON "ScoreBreakdown"("recommendationId");

-- CreateIndex
CREATE UNIQUE INDEX "TechnicalSignal_recommendationId_key" ON "TechnicalSignal"("recommendationId");

-- CreateIndex
CREATE UNIQUE INDEX "FundamentalData_recommendationId_key" ON "FundamentalData"("recommendationId");

-- CreateIndex
CREATE UNIQUE INDEX "SentimentData_recommendationId_key" ON "SentimentData"("recommendationId");

-- AddForeignKey
ALTER TABLE "Recommendation" ADD CONSTRAINT "Recommendation_runId_fkey" FOREIGN KEY ("runId") REFERENCES "PipelineRun"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ScoreBreakdown" ADD CONSTRAINT "ScoreBreakdown_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "Recommendation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TechnicalSignal" ADD CONSTRAINT "TechnicalSignal_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "Recommendation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FundamentalData" ADD CONSTRAINT "FundamentalData_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "Recommendation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SentimentData" ADD CONSTRAINT "SentimentData_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "Recommendation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "LlmOutput" ADD CONSTRAINT "LlmOutput_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "Recommendation"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

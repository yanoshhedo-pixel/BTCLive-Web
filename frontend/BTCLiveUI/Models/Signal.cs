namespace BTCLiveUI.Models
{
    /// <summary>
    /// Signal data model matching backend Signal type
    /// </summary>
    public class Signal
    {
        public string Exchange { get; set; } = string.Empty;
        public string SetupType { get; set; } = string.Empty;
        public long Timestamp { get; set; }
        public double Score { get; set; }
        public double Price { get; set; }
        public double? EntryLevel { get; set; }
        public double? InvalidationLevel { get; set; }
        public double? TargetLevel { get; set; }
        public double Spread { get; set; }
        public double SpreadBps { get; set; }
        public double SlippageEstimate { get; set; }
        public int TtlSeconds { get; set; }
        public string Mode { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public Dictionary<string, object>? Details { get; set; }

        public DateTime DateTime => DateTimeOffset.FromUnixTimeMilliseconds(Timestamp).LocalDateTime;

        public string FormattedPrice => $"${Price:N2}";
        public string FormattedEntry => EntryLevel.HasValue ? $"${EntryLevel.Value:N2}" : "N/A";
        public string FormattedInvalidation => InvalidationLevel.HasValue ? $"${InvalidationLevel.Value:N2}" : "N/A";
        public string FormattedTarget => TargetLevel.HasValue ? $"${TargetLevel.Value:N2}" : "N/A";
        public string FormattedScore => $"{Score:P0}";
        public string FormattedSpread => $"{SpreadBps:F2} bps";
        public string FormattedSlippage => $"{SlippageEstimate:F2} bps";
    }
}

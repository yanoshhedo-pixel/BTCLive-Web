namespace BTCLiveUI.Models
{
    /// <summary>
    /// Alert log entry
    /// </summary>
    public class AlertLog
    {
        public DateTime Timestamp { get; set; }
        public string Exchange { get; set; } = string.Empty;
        public string SetupType { get; set; } = string.Empty;
        public double Score { get; set; }
        public double Price { get; set; }
        public string Status { get; set; } = string.Empty;
        public string Details { get; set; } = string.Empty;

        public string FormattedTimestamp => Timestamp.ToString("HH:mm:ss");
        public string FormattedPrice => $"${Price:N2}";
        public string FormattedScore => $"{Score:P0}";
    }
}

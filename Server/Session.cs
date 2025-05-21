using System.ComponentModel.DataAnnotations;

namespace Server.Models
{
    public class Session
    {
        [Key]
        public int Id { get; set; }
        public DateTime StartTime { get; set; } = DateTime.UtcNow;
        public DateTime? EndTime { get; set; }
        public string Name { get; set; } = "New Session";
        public virtual ICollection<TelemetryPacket> TelemetryPackets { get; set; } = new List<TelemetryPacket>();
    }
}

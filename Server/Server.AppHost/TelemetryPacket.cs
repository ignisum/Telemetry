using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Server.Models
{
    public class TelemetryPacket
    {
        [Key]
        public long Id { get; set; }
        public int Crc16 { get; set; }
        public int PacketCounter { get; set; }
        public double Payload { get; set; }
        public int SyncMarker { get; set; } = 0x12345678;
        public double Timestamp { get; set; }

        [ForeignKey("Session")]
        public long SessionId { get; set; }
        public virtual Session Session { get; set; }
    }
}
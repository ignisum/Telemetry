using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Server.Models
{
    public class TelemetryPacket
    {
        [Key]
        public int Id { get; set; }
        public ushort Crc16 { get; set; }
        public uint PacketCounter { get; set; }
        public double Payload { get; set; }
        public uint SyncMarker { get; set; } = 0x12345678;
        public double Timestamp { get; set; }

        [ForeignKey("Session")]
        public int SessionId { get; set; }
        public virtual Session Session { get; set; }
    }
}
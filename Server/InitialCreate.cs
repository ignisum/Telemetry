using Microsoft.EntityFrameworkCore.Migrations;

namespace Server.Data.Migrations
{
    public class InitialCreate : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Packest",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false),
                    SyncMarker = table.Column<int>(type:"bigint", nullable: false, defaultValue: 0x12345678),
                    PacketCounter = table.Column<long>(type:"bigint", nullable: false),
                    Timestamp = table.Column<double>(type: "double precision", nullable: false),
                    Payload = table.Column<double>(type: "double precision", nullable: false),
                    Crc16 = table.Column<short>(type:"smallint", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Packets", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Packets_Timestamp",
                table: "Packets",
                column: "Timestamp"
                );
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(name: "Packets");
        }
    }
}

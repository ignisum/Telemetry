using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace Server.AppHost.Migrations
{
    /// <inheritdoc />
    public partial class FixIdentityColumns : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE public.""Packets""
                ALTER COLUMN ""Id"" DROP IDENTITY,
                ALTER COLUMN ""Id"" TYPE bigint,
                ALTER COLUMN ""Id"" ADD GENERATED ALWAYS AS IDENTITY;
            ");

            migrationBuilder.Sql(@"
                ALTER TABLE public.""Sessions""
                ALTER COLUMN ""Id"" DROP IDENTITY,
                ALTER COLUMN ""Id"" TYPE bigint,
                ALTER COLUMN ""Id"" ADD GENERATED ALWAYS AS IDENTITY;
            ");
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(@"
                ALTER TABLE public.""Packets""
                ALTER COLUMN ""Id"" DROP IDENTITY,
                ALTER COLUMN ""Id"" TYPE integer,
                ALTER COLUMN ""Id"" ADD GENERATED ALWAYS AS IDENTITY;
            ");

            migrationBuilder.Sql(@"
                ALTER TABLE public.""Sessions""
                ALTER COLUMN ""Id"" DROP IDENTITY,
                ALTER COLUMN ""Id"" TYPE integer,
                ALTER COLUMN ""Id"" ADD GENERATED ALWAYS AS IDENTITY;
            ");
        }
    }
}

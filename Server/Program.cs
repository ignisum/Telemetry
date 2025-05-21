using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Server.Data;
using Server.Hubs;
using Server.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<ApplicationContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("PostgreSQL")));

builder.Services.AddSignalR();
builder.Services.AddControllers();
builder.Services.AddHostedService<TelemetryService>();
builder.Services.AddCors(options =>
    options.AddPolicy("AllowAll", policy => policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));
builder.Services.AddScoped<TelemetryService>();
builder.Services.AddSingleton(provider =>
    provider.GetServices<IHostedService>().OfType<TelemetryService>().First());

var app = builder.Build();

app.UseCors("AllowAll");
app.MapControllers();
app.MapHub<TelemetryHub>("/telemetryhub");

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ApplicationContext>();
    db.Database.Migrate();
}

app.Run();
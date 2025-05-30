var builder = WebApplication.CreateBuilder(args);
builder.Services.AddControllers();
builder.Services.AddScoped<DataProcessingService>();
var app = builder.Build();
app.UseHttpsRedirection();
app.MapControllers();
app.Run();
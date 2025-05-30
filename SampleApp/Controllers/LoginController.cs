using Microsoft.AspNetCore.Mvc;
using SampleApp.Models;

namespace SampleApp.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class LoginController : ControllerBase
    {
        [HttpPost]
        public IActionResult Login(User user)
        {
            // Intentionally insecure logic for demo purposes
            if (user.Username == "admin" && user.Password == "1234")
                return Ok("Logged in!");
            return Unauthorized();
        }
    }
}
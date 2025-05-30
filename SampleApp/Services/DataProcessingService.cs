using System.Threading;

namespace SampleApp.Services
{
    public class DataProcessingService
    {
        public int SlowCalculation(int input)
        {
            // Simulate slow method for dotTrace demo
            Thread.Sleep(1000);
            return input * 2;
        }
    }
}
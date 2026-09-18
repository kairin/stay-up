// Minimal standalone re-implementation of PowerToys Awake's core mechanism,
// referenced from src/modules/awake/Awake/Core/Native/Bridge.cs and
// Core/Manager.cs (SetAwakeState/ComputeAwakeState) in the PowerToys
// repo (MIT licensed, github.com/microsoft/PowerToys).
//
// Usage: StayAwake.exe [--display]
//   --display   also keep the display on (not just prevent system sleep)
//
// Runs until Ctrl+C / window closed; on exit the execution state resets
// automatically because ES_CONTINUOUS is only in effect while this
// process is alive.
using System;
using System.Runtime.InteropServices;
using System.Threading;

internal static class StayAwake
{
    [Flags]
    private enum ExecutionState : uint
    {
        ES_CONTINUOUS = 0x80000000,
        ES_SYSTEM_REQUIRED = 0x00000001,
        ES_DISPLAY_REQUIRED = 0x00000002,
    }

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    private static extern ExecutionState SetThreadExecutionState(ExecutionState esFlags);

    private static void Main(string[] args)
    {
        bool keepDisplayOn = Array.Exists(args, a => a == "--display");

        ExecutionState state = keepDisplayOn
            ? ExecutionState.ES_CONTINUOUS | ExecutionState.ES_SYSTEM_REQUIRED | ExecutionState.ES_DISPLAY_REQUIRED
            : ExecutionState.ES_CONTINUOUS | ExecutionState.ES_SYSTEM_REQUIRED;

        Console.WriteLine("StayAwake running (display kept on: " + keepDisplayOn + "). Press Ctrl+C to exit.");

        Console.CancelKeyPress += (sender, e) =>
        {
            SetThreadExecutionState(ExecutionState.ES_CONTINUOUS);
            Console.WriteLine("StayAwake stopped, normal power state restored.");
        };

        while (true)
        {
            ExecutionState result = SetThreadExecutionState(state);
            if (result == 0)
            {
                Console.WriteLine("SetThreadExecutionState failed, error " + Marshal.GetLastWin32Error());
            }

            Thread.Sleep(30000);
        }
    }
}

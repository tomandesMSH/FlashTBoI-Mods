// TBoI Flash Mods launcher ("TBoI Flash Mods.exe"): starts the modded game in Adobe's Flash Player projector.
//
// Written next to isaac_mods.swf and flashplayer_32_sa.exe by the installer. It ignores its own command-line
// arguments, so it can be used as a Steam launch option ("...\TBoI Flash Mods.exe" %command%): Steam appends the
// original game's path, which the projector would otherwise try to open as the movie. It waits for the
// projector to close, so Steam shows the game as running and counts the playtime.
//
// Build (done by the installer, or by tools/build_exe.py, with the .NET Framework compiler that ships with Windows):
//   csc /target:winexe /optimize /out:"TBoI Flash Mods.exe" FlashModsLauncher.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("TBoI Flash Mods")]
[assembly: AssemblyDescription("Starts The Binding of Isaac (Flash) with the mods chosen in TBoI Flash Mods")]
[assembly: AssemblyProduct("TBoI Flash Mods")]

static class FlashModsLauncher
{
    [STAThread]
    static int Main()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string projector = Path.Combine(dir, "flashplayer_32_sa.exe");
        string swf = Path.Combine(dir, "isaac_mods.swf");
        if (!File.Exists(projector) || !File.Exists(swf))
        {
            MessageBox.Show("flashplayer_32_sa.exe and isaac_mods.swf must be in the same folder as TBoI Flash Mods.exe:\n" + dir +
                            "\n\nRun TBoI Flash Mods again to install the mods.", "TBoI Flash Mods",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        ProcessStartInfo start = new ProcessStartInfo(projector, "\"" + swf + "\"");
        start.WorkingDirectory = dir;
        start.UseShellExecute = false;
        using (Process game = Process.Start(start))
        {
            game.WaitForExit();
            return game.ExitCode;
        }
    }
}

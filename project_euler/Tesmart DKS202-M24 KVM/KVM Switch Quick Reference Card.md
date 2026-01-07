# Tesmart DKS202-M24 KVM Switch Quick Reference Card

**Cluster: FreedomTower Multi-Node Setup**  
**Systems: TheBeast (Dual RTX 5090) ↔ MiniBeast (Dual RTX 4090)**  
**Model: Tesmart DKS202-M24 (2x2 DP 1.4 Dual Monitor KVM)**  
**Date Created:** January 2026  
**Owner:** Peter Heller (ph3ll3r)

---

## System Overview

### Connected Systems
| System | GPU Configuration | Primary GPU | Connected Ports |
|--------|------------------|-------------|-----------------|
| **TheBeast** | Dual RTX 5090 | GPU0 (Top Slot) | PC1 INPUT 1 & 2 |
| **MiniBeast** | Dual RTX 4090 | GPU0 (Top Slot) | PC2 INPUT 1 & 2 |

### Display Configuration
- **Monitor 1:** Connected to KVM OUTPUT 1
- **Monitor 2:** Connected to KVM OUTPUT 2
- **Maximum Resolution:** 8K@60Hz or 4K@144Hz/165Hz per monitor
- **Protocol:** DisplayPort 1.4 (32.4 Gbps bandwidth per port)

---

## Quick Switching Methods

### Method 1: Front Panel Buttons
- **PC1 Button (Orange):** Switch to TheBeast
- **PC2 Button (Orange):** Switch to MiniBeast
- **Physical Location:** Front left panel of KVM

### Method 2: Keyboard Hotkeys (Default)
| Action | Hotkey Combination |
|--------|-------------------|
| Switch to PC1 (TheBeast) | `Right-Ctrl` + `Right-Ctrl` + `1` |
| Switch to PC2 (MiniBeast) | `Right-Ctrl` + `Right-Ctrl` + `2` |
| Enter Hotkey Programming | `Right-Ctrl` + `Right-Ctrl` + `F1` |
| Toggle Keyboard/Mouse Mode | `Right-Ctrl` + `Right-Ctrl` + `F2` |

**Note:** Press `Right-Ctrl` twice quickly, then press the number key.

### Method 3: IR Remote Control
- Use included remote to switch between PC1 and PC2
- Direct line-of-sight required to front panel

### Method 4: Mouse Wheel (If Enabled)
- Scroll mouse wheel while cursor is at screen edge
- Must be enabled in KVM settings

---

## Port Mapping Reference

### Back Panel Connections

```
┌─────────────────────────────────────────────────────────────┐
│                    TESMART DKS202-M24                       │
│                                                             │
│  [Ethernet] [DC 12V]                                       │
│                                                             │
│  PC2 INPUTS          OUTPUT          PC1 INPUTS            │
│  ┌──┬──┐           ┌──┬──┐           ┌──┬──┐             │
│  │IN│IN│   [USB2]  │ 1│ 2│  [USB1]   │IN│IN│             │
│  │ 1│ 2│           └──┴──┘           │ 1│ 2│             │
│  └──┴──┘                              └──┴──┘             │
│  MiniBeast                            TheBeast            │
└─────────────────────────────────────────────────────────────┘
```

### Front Panel Layout

```
┌─────────────────────────────────────────────────┐
│  (●) [USB3.0] [USB3.0] [USB] [USB]  [IR]  [PC2] [PC1]  │
│   │                                    ▼     ▼    │
│  Mic    Peripheral Ports            Buttons     │
│                                                  │
│  [L] [R] [○]                              Status │
│  Audio  Power                             LEDs   │
└─────────────────────────────────────────────────┘
```

### USB Peripheral Setup

**Wenter 11-Port Hub → KVM Front USB 3.0 Port**
- Keyboard
- Mouse  
- SABRENT USB Audio Adapter
- UGREEN USB Audio Adapter
- USB Extension Cables (2×)

**Direct PC Connections (Not Shared via KVM):**
- USB drives/flash drives → Rear motherboard USB ports
- External storage → Rear motherboard USB ports

---

## Cable Specifications

### DisplayPort Cables

| Connection | Cable Type | Length | Specs |
|------------|-----------|--------|-------|
| GPU → KVM Input (×4) | IVANKY 8K DP 1.4 | 6.6ft | 8K@60Hz, 4K@144Hz |
| KVM Output → Monitor (×2) | IVANKY 8K DP 1.4 | 3ft | 8K@60Hz, 4K@144Hz |

**Capabilities:**
- DP 1.4 Protocol
- 32.4 Gbps bandwidth per cable
- HDR, HDCP 2.2, G-Sync, FreeSync
- DSC (Display Stream Compression)

### USB Cables

| Connection | Cable Type | Purpose |
|------------|-----------|---------|
| PC1 → KVM | USB 3.0 Type-A to Type-B | Keyboard/Mouse/Peripherals |
| PC2 → KVM | USB 3.0 Type-A to Type-B | Keyboard/Mouse/Peripherals |

---

## Display Resolution Support

### Supported Resolutions (Per Monitor)

| Resolution | Refresh Rate | Color Depth | Chroma |
|-----------|--------------|-------------|--------|
| 8K (7680×4320) | 60Hz | 10-bit | 4:4:4 |
| 5K (5120×2880) | 60Hz | 10-bit | 4:4:4 |
| 4K (3840×2160) | 165Hz | 8-bit | 4:4:4 |
| 4K (3840×2160) | 144Hz | 10-bit | 4:4:4 |
| 4K (3840×2160) | 120Hz | 10-bit | 4:4:4 |
| 4K (3840×2160) | 60Hz | 10-bit | 4:4:4 |
| 2K (2560×1440) | 240Hz | 8-bit | 4:4:4 |
| 1080p (1920×1080) | 240Hz | 8-bit | 4:4:4 |

---

## EDID Management

### What is EDID?
**Extended Display Identification Data** - Information exchanged between monitor and GPU to establish optimal display settings.

### KVM EDID Features
- **Built-in EDID Emulation:** Enabled by default
- **Purpose:** Prevents Windows from:
  - Resetting resolution when switching
  - Rearranging windows
  - Changing refresh rates
  - Losing display configuration

### EDID Best Practices
1. **Set identical resolution/refresh rate on both PCs** for seamless switching
2. **Configure displays before first switch** to establish EDID baseline
3. **Avoid hot-unplugging monitors** - EDID data may be lost
4. **Use Windows Display Settings** to verify resolution after switching

### Verify EDID Status
```powershell
# Check current display configuration
Get-CimInstance -ClassName Win32_VideoController | 
    Select-Object Name, VideoModeDescription, CurrentRefreshRate
```

---

## Advanced Configuration

### Custom Hotkey Programming

**To Change Trigger Key from Right-Ctrl:**
1. Press and hold front panel `[○]` button for 10 seconds
2. Wait for long beep
3. Press desired new trigger key on keyboard
4. KVM will beep to confirm

**Example:** Change to `Scroll Lock` instead of `Right-Ctrl`

**Note:** This procedure is for hotkey customization only. The KVM does not have a factory reset function.

### Keyboard/Mouse Emulation Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Pass-Through** (Default) | Direct USB device communication | Modern keyboards/mice |
| **Legacy Emulation** | PS/2 emulation mode | Compatibility issues |

**Switch Mode:** `Right-Ctrl` + `Right-Ctrl` + `F2`

**Symptoms requiring Legacy Mode:**
- Keyboard not detected after switch
- Mouse cursor freezing
- Special keys not working (media keys, macros)
- Gaming keyboard lighting sync issues

### Audio Configuration

**Windows Audio Settings (Both PCs):**
1. Open Settings → System → Sound
2. Set **Output Device:** "USB Audio Device"
3. Set **Input Device:** "USB Audio Device" (if using mic)
4. Test audio after KVM switch

**Integrated Audio Ports:**
- **Front Panel:** Mic input, L/R audio output
- **Transmission:** Via USB channel (no separate audio cable needed)

### Network Switch (Built-in)

**Gigabit Ethernet Port:**
- Location: Back panel, left side
- Speed: 1000 Mbps
- Purpose: Share network connection between PCs
- **Note:** Both TheBeast and MiniBeast already on Tailscale VPN - this port is optional

---

## Troubleshooting Guide

### Issue: No Display After Switching

**Possible Causes & Solutions:**

1. **EDID Not Initialized**
   ```
   Solution: Set display configuration on both PCs first
   - Windows Settings → Display
   - Arrange monitors, set resolution/refresh rate
   - Switch to other PC and repeat
   ```

2. **Advanced EDID Diagnostics**
   ```powershell
   # Check current EDID state
   Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorDescriptorMethods
   
   # Verify monitor detection
   Get-CimInstance -ClassName Win32_DesktopMonitor | 
       Select-Object DeviceID, ScreenHeight, ScreenWidth, MonitorType
   
   # Check display adapter status
   Get-CimInstance -ClassName Win32_VideoController | 
       Select-Object Name, Status, VideoModeDescription, 
       @{Name='ActiveOutputs';Expression={$_.CurrentNumberOfColors}}
   
   # Force display re-detection
   # Run as Administrator:
   pnputil /scan-devices
   ```

3. **Cable Connection Loose**
   ```
   Check:
   - GPU DP ports fully seated
   - KVM input ports fully clicked in
   - Monitor input ports secure
   ```

3. **GPU Not Detected**
   ```powershell
   # Verify GPU status
   nvidia-smi -L
   
   # Should show:
   # GPU 0: NVIDIA GeForce RTX 5090 (or 4090)
   # GPU 1: NVIDIA GeForce RTX 5090 (or 4090)
   ```

4. **Wrong GPU Selected**
   ```
   Verify DisplayPort cables connected to GPU 0 (top slot)
   Not GPU 1 (bottom slot)
   ```

### Issue: Windows Rearranges Windows After Switch

**Root Cause:** EDID not properly emulated or different resolutions set

**Solution:**
1. Ensure both PCs have **identical display configuration**:
   - Same resolution (e.g., 4K 3840×2160)
   - Same refresh rate (e.g., 144Hz)
   - Same monitor arrangement (primary/secondary)

2. Disable Windows "Remember Window Positions":
   ```
   Not a Windows setting - use third-party tools like:
   - PowerToys FancyZones
   - DisplayFusion
   ```

3. Re-establish EDID:
   - Disconnect monitors from KVM
   - Connect Monitor 1 directly to TheBeast
   - Configure displays
   - Connect Monitor 1 directly to MiniBeast  
   - Configure displays identically
   - Reconnect to KVM

### Issue: Keyboard/Mouse Not Working

**Solution 1: Switch Emulation Mode**
```
Hotkey: Right-Ctrl + Right-Ctrl + F2
This toggles between Pass-Through and Legacy modes
```

**Solution 2: Re-seat USB Connections**
```
1. Unplug USB Type-B cable from KVM
2. Wait 5 seconds
3. Replug cable
4. Wait for Windows USB detection sound
```

**Solution 3: Check USB Hub Power**
```
Verify Wenter hub power adapter is connected
Hub LED should be illuminated
```

**Solution 4: Try Direct Connection**
```
Temporarily connect keyboard/mouse directly to KVM front ports
Bypass USB hub to isolate issue
```

### Issue: Reduced Refresh Rate (60Hz instead of 144Hz)

**Root Cause:** DP cable bandwidth limitation or incorrect settings

**Check List:**
1. ✓ Using IVANKY 8K DP 1.4 cables (not BENFEI 4K@60Hz cables)
2. ✓ Windows Display Settings show correct refresh rate available
3. ✓ NVIDIA Control Panel → Change Resolution → Refresh Rate set to 144Hz
4. ✓ Monitor OSD menu shows 144Hz mode active

**Force Refresh Rate:**
```
NVIDIA Control Panel:
1. Display → Change Resolution
2. Select 3840 × 2160
3. Refresh Rate: 144Hz
4. Apply
```

### Issue: G-Sync/FreeSync Not Working

**Verification Steps:**

1. **NVIDIA Control Panel:**
   ```
   Display → Set up G-SYNC
   ☑ Enable G-SYNC, G-SYNC Compatible
   ☑ Enable for full screen mode
   Apply
   ```

2. **Monitor OSD:**
   ```
   Navigate to monitor settings
   Enable G-Sync/FreeSync/Adaptive Sync
   ```

3. **Test with Game:**
   ```
   Use NVIDIA GeForce Experience → FPS Counter
   Observe variable frame rate (not capped at refresh rate)
   ```

### Issue: Audio Not Switching with KVM

**Solution 1: Verify USB Audio Device**
```
Windows Settings → Sound
Playback: USB Audio Device (not Realtek or other)
Recording: USB Audio Device
```

**Solution 2: Re-enumerate USB Devices**
```
Device Manager → Sound, video and game controllers
Right-click "USB Audio Device" → Uninstall
Unplug/replug USB hub from KVM
Let Windows reinstall driver
```

**Solution 3: Check Adapter Connection**
```
Verify SABRENT or UGREEN adapter firmly seated in hub
Try different USB port on hub
```

### Issue: Monitors Show "No Signal" After Switch

**Quick Fix:**
```
1. Press KVM front panel button 2-3 times
2. Wait 3 seconds between presses
3. Allows EDID re-negotiation
```

**Deep Fix:**
```
1. Power cycle sequence:
   - Turn off both monitors
   - Press KVM power button (front panel)
   - Wait 10 seconds
   - Press KVM power button to turn on
   - Turn on monitors
   
2. Verify active PC LED on KVM front panel
```

### Issue: One Monitor Works, Other Doesn't

**Check:**
1. Both monitors powered on
2. Both monitors on correct input (DisplayPort)
3. Swap monitor cables at KVM OUTPUT to isolate bad cable
4. Verify GPU has dual display enabled in BIOS/UEFI

**GPU Multi-Monitor Check:**
```powershell
# Verify Windows sees both displays
Get-CimInstance -ClassName Win32_DesktopMonitor | 
    Select-Object DeviceID, ScreenHeight, ScreenWidth
```

---

## Advanced Signal Diagnostics

### DisplayPort Signal Testing

**Verify DP Signal Integrity:**
```powershell
# Check GPU DisplayPort output status
# NVIDIA-specific query
nvidia-smi --query-gpu=index,name,display_active,display_mode --format=csv

# Alternative: Check via WDDM
Get-CimInstance -ClassName Win32_VideoController | 
    Select-Object Name, VideoProcessor, 
    @{Name='ActivePorts';Expression={
        $_.VideoMemoryType -ne $null
    }}
```

**Monitor DisplayPort Link Training:**
```
Use monitor OSD to check:
- Current connection type (DisplayPort 1.4)
- Active resolution and refresh rate
- Color format (RGB 4:4:4 vs YCbCr)
- Bit depth (8-bit vs 10-bit)

Many monitors show this in:
OSD → Information → Input Signal
```

**Cable Quality Test:**
```
Test sequence for each DP cable:
1. Connect cable directly (GPU → Monitor, bypass KVM)
2. Set to maximum resolution/refresh (4K@144Hz or 8K@60Hz)
3. Run TestUFO motion test (testufo.com) for 5 minutes
4. Check for:
   - Sparkles/snow on screen
   - Signal dropouts
   - Intermittent black screens
   
If issues occur direct connection:
   → Cable is faulty, replace
If issues only occur through KVM:
   → Contact Tesmart support
```

### USB Signal Diagnostics

**Verify USB Hub Enumeration:**
```powershell
# List all USB devices and their power states
Get-PnpDevice -Class USB | 
    Select-Object FriendlyName, Status, InstanceId | 
    Where-Object {$_.Status -ne "Unknown"} |
    Format-Table -AutoSize

# Check USB controller status
Get-PnpDevice -Class USB | Where-Object {
    $_.FriendlyName -like "*USB*Host Controller*"
} | Select-Object FriendlyName, Status

# Verify USB 3.0 SuperSpeed enumeration
# KVM should appear as USB 3.0 (5 Gbps)
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Enum\USB\*" -ErrorAction SilentlyContinue |
    Where-Object {$_.DeviceDesc -like "*KVM*" -or $_.DeviceDesc -like "*Hub*"} |
    Select-Object DeviceDesc, Service
```

**Test USB Bandwidth:**
```
Method 1: Use CrystalDiskMark with USB flash drive
- Connect USB drive to hub
- Run sequential read/write test
- USB 3.0: Should achieve 100+ MB/s read
- USB 2.0: Will cap at ~35 MB/s read

Method 2: Check Device Manager
- Device Manager → USB controllers
- Expand "Generic USB Hub"
- Properties → Advanced → "Hub is bus powered: No"
  (KVM hub should show as self-powered if external hub is used)
```

### Network Diagnostics (Built-in Gigabit Switch)

**If using KVM's built-in network port:**
```powershell
# Test network throughput
# From TheBeast, test to known server
Test-NetConnection -ComputerName 192.168.1.1 -TraceRoute

# Verify gigabit link speed
Get-NetAdapter | Where-Object {$_.Status -eq "Up"} |
    Select-Object Name, LinkSpeed, MediaType

# Should show: LinkSpeed = 1 Gbps

# Test actual throughput (requires iperf3)
# Server: iperf3 -s
# Client: iperf3 -c <server_ip> -t 30
# Should achieve 900+ Mbps
```

---

## Performance Verification

### Display Performance Test

**Test 1: Refresh Rate Verification**
```
Website: testufo.com
1. Navigate to TestUFO Motion Tests
2. Run "Framerate" test
3. Verify actual vs. expected FPS matches
4. Should show 144 FPS for 144Hz, 60 FPS for 60Hz
```

**Test 2: Pixel Response**
```
Website: testufo.com/ghosting
1. Run ghosting test
2. Check for:
   - Clean edges on moving objects
   - No trailing/smearing
   - Smooth motion
```

**Test 3: Input Latency**
```
Human perception test:
- Move mouse cursor in circles
- Click/drag windows rapidly
- Should feel identical to direct GPU connection
- No perceptible delay
```

### GPU Performance Verification

**Confirm Primary GPU Active:**
```powershell
# Run on current active PC
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv

# Expected output shows GPU 0 driving displays
# GPU 1 should show 0% utilization (unless running compute tasks)
```

**Display Adapter Check:**
```powershell
Get-CimInstance -ClassName Win32_VideoController | 
    Where-Object {$_.Name -like "*NVIDIA*"} |
    Select-Object Name, AdapterRAM, VideoModeDescription, DriverVersion |
    Format-Table -AutoSize
```

### Bandwidth Test

**4K@144Hz Bandwidth Calculation:**
```
Formula: (Width × Height × Refresh × Color Depth) / Compression

Example 4K@144Hz 10-bit:
(3840 × 2160 × 144 × 30 bits) / 1.5 (DSC) = 23.9 Gbps
✓ Within DP 1.4 limit of 32.4 Gbps
```

**Verify No Compression Artifacts:**
- Display solid color test patterns
- Check for banding, dithering, or color shifts
- Compare switched display vs. direct GPU connection

---

## Maintenance & Best Practices

### Daily Operations

**Switching Between Systems:**
1. Save all work before switching
2. Use hotkey or front button
3. Wait 2-3 seconds for displays to sync
4. Verify both monitors active before proceeding

**Audio Switching:**
- Audio follows KVM switch automatically
- If no audio, check Windows Sound settings (USB Audio Device)

### Weekly Checks

- ✓ Verify all cables firmly seated
- ✓ Check KVM LEDs indicate correct active PC
- ✓ Test switch between PCs at least once
- ✓ Confirm resolution/refresh rate maintained

### Monthly Maintenance

- ✓ Clean KVM vents (dust accumulation)
- ✓ Verify firmware (check Tesmart support site)
- ✓ Test all 4 switching methods (button, hotkey, remote, mouse)
- ✓ Backup display profiles on both PCs

### Cable Management

**Organization:**
- Bundle PC1 cables separately from PC2 cables
- Label cables at both ends (e.g., "TheBeast-DP1", "MiniBeast-DP2")
- Use velcro ties, not zip ties (allows re-routing)
- Leave some slack for maintenance access

**Strain Relief:**
- Don't over-bend DisplayPort cables (max 90° bend)
- Support cable weight with cable management clips
- Keep cables away from power cables (EMI prevention)

### Firmware Updates

**Check for Updates:**
```
Website: support.tesmart.com
Navigate to: Products → DKS202-M24 → Firmware

Current Version: Check KVM sticker or manual
Update Method: USB firmware updater (Windows/Mac tool)
```

**Update Procedure:**
1. Download latest firmware from Tesmart support
2. Connect KVM to PC via USB (special firmware update cable may be required)
3. Run firmware updater tool
4. Follow on-screen instructions
5. Do not power off KVM during update

---

## System Specifications

### KVM Technical Specs

| Specification | Value |
|--------------|-------|
| Model | Tesmart DKS202-M24 |
| Input Ports | 2 PCs × 2 DP 1.4 ports each |
| Output Ports | 2 monitors (DP 1.4) |
| Video Protocol | DisplayPort 1.4 |
| Bandwidth | 32.4 Gbps per port |
| Max Resolution | 8K@60Hz, 4K@165Hz |
| USB Ports | USB 3.0 (5 Gbps) |
| Front Panel USB | 4× USB 3.0 Type-A ports |
| Audio | Integrated mic in, L/R audio out |
| Network | 1× Gigabit Ethernet |
| Power | 12V DC adapter (included) |
| EDID Emulation | Yes (built-in) |
| Dimensions | ~295mm × 100mm × 40mm |
| Weight | ~1.2 kg |

### Connected System Specs

**TheBeast:**
- GPU: 2× NVIDIA RTX 5090 (GPU0 = primary display)
- DisplayPorts Used: GPU0 DP1, GPU0 DP2
- USB: Rear motherboard port → KVM PC1
- Purpose: Primary workstation, AI compute

**MiniBeast:**
- GPU: 2× NVIDIA RTX 4090 (GPU0 = primary display)  
- DisplayPorts Used: GPU0 DP1, GPU0 DP2
- USB: Rear motherboard port → KVM PC2
- Purpose: Secondary workstation, AI compute

---

## Hotkey Quick Reference

### Essential Hotkeys

| Function | Hotkey |
|----------|--------|
| Switch to PC1 (TheBeast) | `Right-Ctrl` `Right-Ctrl` `1` |
| Switch to PC2 (MiniBeast) | `Right-Ctrl` `Right-Ctrl` `2` |
| Toggle Keyboard/Mouse Mode | `Right-Ctrl` `Right-Ctrl` `F2` |
| Enter Custom Hotkey Setup | Hold front `[○]` button 10 sec |

### Extended Hotkeys (If Supported)

| Function | Hotkey |
|----------|--------|
| Cycle Through PCs | `Right-Ctrl` `Right-Ctrl` `Enter` |
| Audio Mute Toggle | `Right-Ctrl` `Right-Ctrl` `M` |
| Show Active PC | `Right-Ctrl` `Right-Ctrl` `I` |

**Note:** Extended hotkeys availability depends on firmware version. Check manual for complete list.

---

## Emergency Procedures

### Display Completely Black - Both Monitors

**Emergency Recovery:**
1. **Power Cycle Everything:**
   ```
   - Turn off both monitors
   - Unplug KVM power adapter
   - Wait 30 seconds
   - Plug in KVM power
   - Turn on monitors
   - Press PC1 button on KVM
   ```

2. **If Still No Display:**
   ```
   - Disconnect one monitor cable from KVM OUTPUT
   - Connect directly to TheBeast GPU0 DP1
   - Verify GPU/PC is functioning
   - If display works, issue is KVM-related
   - If no display, issue is PC/GPU-related
   ```

3. **Check Active PC:**
   ```
   - Look at front panel LEDs
   - Orange LED should indicate active PC
   - If no LED lit, KVM may not be receiving power
   ```

### Cannot Switch Between PCs

**Troubleshooting Steps:**

1. **Verify USB Connection:**
   ```
   - Check USB Type-B cables connected to both PCs
   - Try unplugging and re-seating
   - Switch using front panel button (not hotkey)
   ```

2. **Reset KVM Power:**
   ```
   - Unplug KVM power
   - Unplug both USB cables from KVM
   - Wait 30 seconds  
   - Reconnect power
   - Reconnect USB cables
   - Try switching again
   ```

3. **Advanced Diagnostics:**
   ```powershell
   # Check USB enumeration on active PC
   Get-PnpDevice -Class USB | Where-Object {$_.Status -eq "OK"} | 
       Select-Object FriendlyName, InstanceId | Format-Table
   
   # Check for USB errors in Event Viewer
   Get-EventLog -LogName System -Source "USB" -Newest 50 | 
       Where-Object {$_.EntryType -eq "Error"}
   
   # Verify HID devices
   Get-PnpDevice -Class HIDClass | Select-Object FriendlyName, Status
   ```

4. **Contact Tesmart Support:**
   ```
   If KVM still not responding:
   - Email: service@tesmart.com
   - Support ticket: https://support.tesmart.com
   - Provide: Model (DKS202-M24), purchase date, issue description
   - Note: KVM does not have a factory reset function
   ```

### Keyboard/Mouse Frozen After Switch

**Quick Fix:**
```
1. Press Right-Ctrl + Right-Ctrl + F2 (toggle emulation mode)
2. Wait 3 seconds
3. If still frozen, unplug USB hub from KVM
4. Wait 5 seconds
5. Replug USB hub
6. Windows should re-enumerate devices
```

### One Monitor Much Dimmer Than Other

**Possible Causes:**

1. **HDR Mismatch:**
   ```
   Windows Settings → Display → HDR
   Ensure both monitors have identical HDR settings
   Either both ON or both OFF
   ```

2. **Monitor Brightness Settings:**
   ```
   Use monitor OSD to check brightness/contrast
   Set identical values on both monitors
   ```

3. **DP Cable Quality:**
   ```
   Swap the two monitor output cables
   If dimness follows cable, replace cable
   If dimness stays with monitor, check monitor settings
   ```

---

## Support Resources

### Tesmart Support

**Website:** https://support.tesmart.com  
**Email:** service@tesmart.com  
**Documentation:** https://support.tesmart.com/hc/en-us/articles/32098347430937

**Manual PDF:** UART-DKS202-M24-V003.pdf  
**QR Code:** Scan QR code on user manual page 2 or back cover

### Driver Downloads

**NVIDIA GPU Drivers:**
- Website: https://www.nvidia.com/Download/index.aspx
- Select: RTX 5090 or RTX 4090
- OS: Windows 11 64-bit
- Update via GeForce Experience or manual download

**USB Audio Drivers:**
- Typically use Windows built-in USB Audio Class driver
- No separate driver installation required
- If issues, check Windows Update for optional driver updates

### Cluster Documentation

**Related Documents:**
- `Cluster_Infrastructure_Overview.md`
- `TheBeast_System_Configuration.md`
- `MiniBeast_System_Configuration.md`
- `Tailscale_VPN_Configuration.md`
- `GPU_Compute_Workload_Distribution.md`

---

## Appendix A: Display Resolution Reference

### Common Gaming Resolutions

| Resolution | Aspect Ratio | Pixels | Common Names |
|-----------|--------------|---------|--------------|
| 1920×1080 | 16:9 | 2.1M | 1080p, Full HD, FHD |
| 2560×1440 | 16:9 | 3.7M | 1440p, QHD, 2K |
| 3840×2160 | 16:9 | 8.3M | 4K, UHD, 2160p |
| 5120×2880 | 16:9 | 14.7M | 5K |
| 7680×4320 | 16:9 | 33.2M | 8K, UHD-2 |

### Ultrawide Resolutions

| Resolution | Aspect Ratio | Pixels | Common Names |
|-----------|--------------|---------|--------------|
| 2560×1080 | 21:9 | 2.8M | UW-FHD |
| 3440×1440 | 21:9 | 5.0M | UW-QHD |
| 5120×2160 | 21:9 | 11.1M | 5K2K |

---

## Appendix B: DP 1.4 Bandwidth Calculator

### Maximum Configurations

**Without DSC (Display Stream Compression):**
```
8K@60Hz 10-bit 4:4:4  = 31.8 Gbps ✓
8K@60Hz 10-bit 4:2:0  = 21.1 Gbps ✓
4K@144Hz 10-bit 4:4:4 = 28.8 Gbps ✓
4K@165Hz 10-bit 4:4:4 = 33.0 Gbps ✗ (requires DSC)
4K@240Hz 8-bit 4:4:4  = 37.8 Gbps ✗ (requires DSC)
```

**With DSC (Typically 3:1 compression):**
```
4K@165Hz 10-bit 4:4:4 = 11.0 Gbps ✓
4K@240Hz 10-bit 4:4:4 = 15.8 Gbps ✓
8K@120Hz 10-bit 4:4:4 = 21.2 Gbps ✓
```

**Formula:**
```
Bandwidth = (Width × Height × Refresh × Color Depth × 3 channels) / Compression

Example for 4K@144Hz 10-bit:
(3840 × 2160 × 144 × 10 × 3) / 1.0 = 28.8 Gbps
```

---

## Appendix C: Windows Display Settings Optimization

### NVIDIA Control Panel Settings

**For Gaming/High Refresh Rate:**
```
Display → Change Resolution:
  ✓ 3840 × 2160
  ✓ 144Hz refresh rate
  ✓ Full (native) color depth
  ✓ RGB (full dynamic range)

Display → Adjust desktop color settings:
  ✓ Use NVIDIA settings
  ✓ Output dynamic range: Full

3D Settings → Manage 3D Settings:
  ✓ Vertical sync: Use application setting
  ✓ Low Latency Mode: Ultra (for gaming)
  ✓ Power management mode: Prefer maximum performance
```

**For Content Creation/Color Accuracy:**
```
Display → Change Resolution:
  ✓ 3840 × 2160
  ✓ 60Hz refresh rate
  ✓ 10-bit color depth
  ✓ RGB (full dynamic range)

Display → Adjust desktop color settings:
  ✓ Use NVIDIA settings
  ✓ Digital vibrance: 50% (neutral)
```

### Windows Display Settings

**Recommended Configuration:**
```
Settings → System → Display:

Scale and layout:
  ✓ Change the size of text, apps: 100% or 125%
  ✓ Display resolution: 3840 × 2160

Multiple displays:
  ✓ Extend desktop to both monitors
  ✓ Make this my main display (select primary monitor)
  ✓ Remember window positions: OFF (reduces issues)

Graphics:
  ✓ Hardware-accelerated GPU scheduling: ON
  ✓ Optimize for windowed games: ON (if gaming)
```

### Monitor OSD Recommended Settings

**For Both Monitors (Keep Identical):**
```
Picture Settings:
  ✓ Picture Mode: Standard or User
  ✓ Brightness: 75-80 (to preference)
  ✓ Contrast: 70-75
  ✓ Sharpness: 50 (neutral)
  ✓ Color Temperature: 6500K (neutral)

Gaming Settings (if applicable):
  ✓ Response Time: Fast or Faster
  ✓ Black Equalizer: 10-15
  ✓ FreeSync/G-Sync: ON
  ✓ Low Input Lag: ON
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-06 | Peter Heller | Initial creation for TheBeast/MiniBeast KVM setup |
| 1.1 | 2026-01-06 | Peter Heller | Corrections based on Tesmart support feedback (Kelly): Removed incorrect factory reset procedure (KVM has no reset function), added advanced diagnostics (EDID, USB, DisplayPort signal testing), enhanced troubleshooting with PowerShell commands |

---

## Contact Information

**Cluster Owner:** Peter Heller  
**GitHub:** ph3ll3r (personal), QCadjunct (educational)  
**System Location:** FreedomTower Multi-Node Cluster  
**Network:** Tailscale VPN across all nodes

---

**END OF QUICK REFERENCE CARD**
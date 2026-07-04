# DiscPrint

A macOS native SwiftUI application for printing images onto printable discs (CD/DVD/Blu-ray) using the Canon TS8300's disc tray attachment.

## Requirements

- macOS 13 Ventura or later
- Xcode 15 or later
- Canon TS8300 printer with official macOS drivers installed
- Canon disc tray accessory

## Opening in Xcode

Double-click **`DiscPrint.xcodeproj`** to open the project in Xcode.

Alternatively, open `Package.swift` via **File ▸ Open** in Xcode — Swift Package Manager will resolve the project automatically.

## Features

| Feature | Description |
|---|---|
| **Image import** | Open via File menu / drag-and-drop. Supports JPEG, PNG, TIFF, HEIC, RAW, BMP, GIF, WebP |
| **Fill modes** | Fit / Fill / Stretch |
| **Scale** | 0.1× – 4× slider |
| **Rotation** | −180° – +180° slider |
| **X/Y position** | Drag image on canvas or use sliders / nudge buttons |
| **Border ring** | Configurable width (mm) and colour |
| **Hub indicator** | Non-printable inner hub (≈38 mm) shown with dashed overlay |
| **Presets** | Save & restore named layout configurations |
| **Export** | Save composited disc image as PNG at 300 dpi |
| **Print** | Sends directly to Canon TS8300 with disc tray media settings |

## Project Structure

```
DiscPrint/
├── DiscPrint.xcodeproj/    ← Open this in Xcode
├── Package.swift           ← Alternative SPM entry point
├── Info.plist
├── DiscPrint.entitlements
└── Sources/
    ├── App/
    │   └── DiscPrintApp.swift       Entry point (@main)
    ├── Views/
    │   ├── ContentView.swift        Main window layout
    │   ├── DiscCanvasView.swift     Interactive disc canvas (drag to position)
    │   ├── ControlsPanel.swift      Sliders, pickers, nudge buttons
    │   └── PrintPreviewView.swift   Read-only print preview
    ├── Models/
    │   ├── DiscLayout.swift         Layout state (scale, offset, rotation, border)
    │   └── Preset.swift             Named preset model
    ├── Services/
    │   ├── ImageImporter.swift      File open panel + drag-and-drop
    │   ├── PrintManager.swift       NSPrintInfo / NSPrintOperation + export
    │   ├── PresetStore.swift        JSON persistence for presets
    │   └── DiscRenderer.swift       Core rendering (shared by canvas + print)
    └── Resources/
        └── Assets.xcassets/
```

## Printer Setup Notes

The app auto-detects the Canon TS8300 by name. If not found it shows a warning but still allows printing via the system default printer.

The app requests the `cd-tray` media source via CUPS job attributes. You must have the **Canon TS8300 Series** drivers installed from Canon's website for this to work correctly.

**Paper size**: The app sets the paper size to `Disc_L` (119 × 119 mm) which is the disc tray page size defined in Canon's PPD.

## Disc Dimensions (Canon TS8300)

| Zone | Diameter |
|---|---|
| Outer printable | 116 mm |
| Inner hub (non-printable) | ~38 mm |
| Tray page size | 119 × 119 mm |

## Building

```bash
# Build from command line (requires Xcode Command Line Tools)
xcodebuild -project DiscPrint.xcodeproj -scheme DiscPrint -configuration Release build
```

## Signing

Set your Apple Developer Team ID in Xcode's target **Signing & Capabilities** tab. The entitlements file already includes the required `com.apple.security.print` entitlement.

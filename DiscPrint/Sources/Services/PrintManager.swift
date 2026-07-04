import AppKit
import Foundation

/// Configures NSPrintInfo for Canon TS8300 disc printing and drives NSPrintOperation.
final class PrintManager {

    // MARK: - Canon TS8300 constants
    /// The PPD paper size name for disc media on Canon TS8300.
    private static let discPaperName = "Disc_L"
    /// Physical square page size for the disc tray (119 × 119 mm in points at 72 dpi).
    private static let discPageSizePt = NSSize(
        width:  mmToPoints(119),
        height: mmToPoints(119)
    )
    /// Printer name fragment used to detect the Canon TS8300.
    private static let canonPrinterFragment = "TS8300"

    // MARK: - Printer detection

    /// Returns the first NSPrinter that looks like a Canon TS8300, or nil.
    static func canonPrinter() -> NSPrinter? {
        NSPrinter.printerNames
            .compactMap { NSPrinter(name: $0) }
            .first { $0.name.localizedCaseInsensitiveContains(canonPrinterFragment) }
    }

    // MARK: - NSPrintInfo setup

    /// Builds a configured NSPrintInfo for disc printing.
    /// - Parameter printer: The Canon TS8300 NSPrinter (uses default printer if nil with a warning).
    /// - Returns: Configured NSPrintInfo.
    static func buildPrintInfo(printer: NSPrinter?) -> NSPrintInfo {
        let info = NSPrintInfo.shared.copy() as! NSPrintInfo

        // Use the Canon printer if available
        if let printer = printer {
            info.printer = printer
        }

        // Set page size to disc
        info.paperSize = discPageSizePt
        info.paperName = NSPrinter.PaperName(discPaperName)

        // Remove default margins — the entire page is the disc tray area
        info.topMargin    = 0
        info.bottomMargin = 0
        info.leftMargin   = 0
        info.rightMargin  = 0

        info.isHorizontallyCentered = false
        info.isVerticallyCentered   = false
        info.scalingFactor          = 1.0
        info.orientation            = .portrait

        // Request the CD tray media source via CUPS job attributes
        info.printSettings[NSPrintInfo.AttributeKey("media-source")] = "cd-tray" as AnyObject
        info.printSettings[NSPrintInfo.AttributeKey("MediaType")]     = "CD" as AnyObject

        return info
    }

    // MARK: - Printing

    /// Renders the disc layout to a view and sends it to the printer.
    /// - Parameters:
    ///   - image: The source image to print.
    ///   - layout: Current disc layout parameters.
    ///   - parentWindow: The window to attach the print sheet to.
    @MainActor
    static func print(image: NSImage, layout: DiscLayout, in parentWindow: NSWindow?) {
        let printer  = canonPrinter()
        let printInfo = buildPrintInfo(printer: printer)

        if printer == nil {
            let alert = NSAlert()
            alert.messageText = "Printer Not Found"
            alert.informativeText = "Could not find a Canon TS8300. The default printer will be used. Make sure the printer is connected and drivers are installed."
            alert.alertStyle = .warning
            alert.addButton(withTitle: "Continue")
            alert.addButton(withTitle: "Cancel")
            if alert.runModal() == .alertSecondButtonReturn { return }
        }

        let printView = DiscPrintView(image: image, layout: layout, pageSize: printInfo.paperSize)
        let operation = NSPrintOperation(view: printView, printInfo: printInfo)
        operation.showsPrintPanel   = true
        operation.showsProgressPanel = true

        if let window = parentWindow {
            operation.runModal(for: window, delegate: nil, didRun: nil, contextInfo: nil)
        } else {
            operation.run()
        }
    }

    // MARK: - Export

    /// Renders the disc composition to a CGImage at the given DPI.
    static func renderDiscImage(image: NSImage, layout: DiscLayout, dpi: CGFloat = 300) -> NSImage? {
        let outerDiameterPt = mmToPoints(DiscLayout.outerRadiusMM * 2)
        let scale = dpi / 72.0
        let pixelSize = NSSize(
            width:  outerDiameterPt * scale,
            height: outerDiameterPt * scale
        )

        let rep = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: Int(pixelSize.width),
            pixelsHigh: Int(pixelSize.height),
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .calibratedRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        )
        guard let rep = rep else { return nil }

        let ctx = NSGraphicsContext(bitmapImageRep: rep)
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = ctx

        let rect = NSRect(origin: .zero, size: pixelSize)
        DiscRenderer.draw(image: image, layout: layout, in: rect)

        NSGraphicsContext.restoreGraphicsState()

        let output = NSImage(size: pixelSize)
        output.addRepresentation(rep)
        return output
    }

    // MARK: - Helpers

    static func mmToPoints(_ mm: Double) -> CGFloat {
        CGFloat(mm) * 72.0 / 25.4
    }
}

// MARK: - NSView subclass used for NSPrintOperation

private final class DiscPrintView: NSView {
    private let image: NSImage
    private let layout: DiscLayout

    init(image: NSImage, layout: DiscLayout, pageSize: NSSize) {
        self.image  = image
        self.layout = layout
        super.init(frame: NSRect(origin: .zero, size: pageSize))
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) not supported") }

    override var isFlipped: Bool { false }

    override func draw(_ dirtyRect: NSRect) {
        DiscRenderer.draw(image: image, layout: layout, in: bounds)
    }
}

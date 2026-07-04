import SwiftUI
import AppKit

/// An NSViewRepresentable that wraps an NSView rendering the disc composition
/// and supports drag-to-reposition.
struct DiscCanvasView: NSViewRepresentable {
    let image: NSImage
    @Binding var layout: DiscLayout

    func makeNSView(context: Context) -> DiscCanvasNSView {
        let view = DiscCanvasNSView()
        view.onLayoutChange = { layout = $0 }
        return view
    }

    func updateNSView(_ nsView: DiscCanvasNSView, context: Context) {
        nsView.image  = image
        nsView.layout = layout
        nsView.needsDisplay = true
    }
}

// MARK: - Underlying NSView

final class DiscCanvasNSView: NSView {
    var image: NSImage?
    var layout: DiscLayout = DiscLayout() { didSet { needsDisplay = true } }
    var onLayoutChange: ((DiscLayout) -> Void)?

    private var dragStart: CGPoint?
    private var layoutAtDragStart: DiscLayout?

    override var isFlipped: Bool { true }
    override var acceptsFirstResponder: Bool { true }

    // MARK: Drawing

    override func draw(_ dirtyRect: NSRect) {
        guard let image = image else {
            drawPlaceholder(in: dirtyRect)
            return
        }

        let center = CGPoint(x: bounds.midX, y: bounds.midY)
        let outerRadius = min(bounds.width, bounds.height) / 2

        // Checkerboard background (shows transparency)
        drawCheckerboard(in: bounds)

        // Disc composition
        DiscRenderer.draw(image: image, layout: layout, in: bounds)

        // Hub guide ring (grey, non-printable zone indicator)
        let innerRadius = outerRadius * CGFloat(DiscLayout.innerRadiusMM / DiscLayout.outerRadiusMM)
        let hubRect = CGRect(
            x: center.x - innerRadius, y: center.y - innerRadius,
            width: innerRadius * 2, height: innerRadius * 2
        )
        NSColor.systemGray.withAlphaComponent(0.35).setFill()
        NSBezierPath(ovalIn: hubRect).fill()

        let dashStyle = [4.0, 4.0] as [CGFloat]
        NSColor.systemGray.setStroke()
        let ring = NSBezierPath(ovalIn: hubRect)
        ring.lineWidth = 1
        ring.setLineDash(dashStyle, count: 2, phase: 0)
        ring.stroke()

        // Hub label
        let attr: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 10),
            .foregroundColor: NSColor.secondaryLabelColor
        ]
        let label = NSAttributedString(string: "Hub", attributes: attr)
        let labelSize = label.size()
        label.draw(at: CGPoint(x: center.x - labelSize.width / 2,
                               y: center.y - labelSize.height / 2))
    }

    private func drawPlaceholder(in rect: NSRect) {
        NSColor.controlBackgroundColor.setFill()
        rect.fill()
    }

    private func drawCheckerboard(in rect: NSRect) {
        let size: CGFloat = 12
        for row in 0...Int(rect.height / size) {
            for col in 0...Int(rect.width / size) {
                let color: NSColor = (row + col) % 2 == 0
                    ? NSColor.systemGray.withAlphaComponent(0.1)
                    : NSColor.systemGray.withAlphaComponent(0.05)
                color.setFill()
                CGRect(x: CGFloat(col) * size, y: CGFloat(row) * size, width: size, height: size).fill()
            }
        }
    }

    // MARK: Drag to reposition

    override func mouseDown(with event: NSEvent) {
        dragStart = convert(event.locationInWindow, from: nil)
        layoutAtDragStart = layout
    }

    override func mouseDragged(with event: NSEvent) {
        guard let start = dragStart, let base = layoutAtDragStart else { return }
        let current = convert(event.locationInWindow, from: nil)
        let radius = min(bounds.width, bounds.height) / 2

        let deltaX = (current.x - start.x) / radius
        let deltaY = (current.y - start.y) / radius

        var updated = base
        updated.offsetX = (base.offsetX + deltaX).clamped(to: -1...1)
        updated.offsetY = (base.offsetY - deltaY).clamped(to: -1...1)  // flip Y (isFlipped)
        layout = updated
        onLayoutChange?(updated)
    }

    override func mouseUp(with event: NSEvent) {
        dragStart = nil
        layoutAtDragStart = nil
    }
}

// MARK: - Comparable clamping helper

extension Comparable {
    func clamped(to range: ClosedRange<Self>) -> Self {
        min(max(self, range.lowerBound), range.upperBound)
    }
}

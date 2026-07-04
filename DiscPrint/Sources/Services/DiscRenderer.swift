import AppKit
import CoreGraphics

/// Pure rendering logic — draws the disc composition into the current NSGraphicsContext.
/// Used by both the on-screen SwiftUI preview and the print/export pipeline.
enum DiscRenderer {

    /// Draw the composited disc into `rect` using the current graphics context.
    static func draw(image: NSImage, layout: DiscLayout, in rect: CGRect) {
        guard let ctx = NSGraphicsContext.current?.cgContext else { return }

        let center = CGPoint(x: rect.midX, y: rect.midY)
        let outerRadius = min(rect.width, rect.height) / 2
        let innerRadius = outerRadius * CGFloat(DiscLayout.innerRadiusMM / DiscLayout.outerRadiusMM)

        ctx.saveGState()

        // --- Clip to outer circle ---
        let outerPath = CGMutablePath()
        outerPath.addEllipse(in: CGRect(
            x: center.x - outerRadius, y: center.y - outerRadius,
            width: outerRadius * 2, height: outerRadius * 2
        ))
        ctx.addPath(outerPath)
        ctx.clip()

        // --- Draw the image ---
        let imgSize = image.size
        let drawRect = imageRect(
            imageSize: imgSize,
            discRect: CGRect(x: center.x - outerRadius, y: center.y - outerRadius,
                             width: outerRadius * 2, height: outerRadius * 2),
            layout: layout
        )

        ctx.saveGState()
        ctx.translateBy(x: center.x, y: center.y)
        ctx.rotate(by: CGFloat(layout.rotation) * .pi / 180)
        ctx.translateBy(x: -center.x, y: -center.y)

        image.draw(in: drawRect,
                   from: .zero,
                   operation: .sourceOver,
                   fraction: 1.0)

        ctx.restoreGState()

        // --- Draw border ring ---
        if layout.borderWidthMM > 0 {
            let borderWidth = outerRadius * CGFloat(layout.borderWidthMM / DiscLayout.outerRadiusMM)
            let borderColor = layout.borderNSColor.cgColor
            ctx.setStrokeColor(borderColor)
            ctx.setLineWidth(borderWidth * 2)  // stroke is centred on the path edge
            ctx.addEllipse(in: CGRect(
                x: center.x - outerRadius, y: center.y - outerRadius,
                width: outerRadius * 2, height: outerRadius * 2
            ))
            ctx.strokePath()
        }

        ctx.restoreGState()

        // --- Draw inner hub mask (clear hole) ---
        ctx.saveGState()
        ctx.setBlendMode(.clear)
        ctx.fillEllipse(in: CGRect(
            x: center.x - innerRadius, y: center.y - innerRadius,
            width: innerRadius * 2, height: innerRadius * 2
        ))
        ctx.restoreGState()
    }

    // MARK: - Image rect calculation

    private static func imageRect(imageSize: CGSize, discRect: CGRect, layout: DiscLayout) -> CGRect {
        let discSize = discRect.size
        let scaledSize: CGSize

        switch layout.fillMode {
        case .fit:
            let factor = min(discSize.width / imageSize.width, discSize.height / imageSize.height)
            scaledSize = CGSize(width: imageSize.width * factor, height: imageSize.height * factor)
        case .fill:
            let factor = max(discSize.width / imageSize.width, discSize.height / imageSize.height)
            scaledSize = CGSize(width: imageSize.width * factor, height: imageSize.height * factor)
        case .stretch:
            scaledSize = discSize
        }

        let userScale = CGFloat(layout.scale)
        let finalSize = CGSize(width: scaledSize.width * userScale, height: scaledSize.height * userScale)

        let discRadius = min(discSize.width, discSize.height) / 2
        let offsetX = CGFloat(layout.offsetX) * discRadius
        let offsetY = CGFloat(layout.offsetY) * discRadius

        let origin = CGPoint(
            x: discRect.midX - finalSize.width  / 2 + offsetX,
            y: discRect.midY - finalSize.height / 2 + offsetY
        )

        return CGRect(origin: origin, size: finalSize)
    }
}

import SwiftUI

/// A read-only full-page preview of how the disc image will appear when printed.
struct PrintPreviewView: View {
    let image: NSImage
    let layout: DiscLayout

    var body: some View {
        VStack(spacing: 16) {
            Text("Print Preview")
                .font(.headline)

            ZStack {
                Color.white
                    .shadow(radius: 6)

                DiscCanvasView(image: image, layout: .constant(layout))
                    .frame(width: 300, height: 300)
                    .padding(20)
            }
            .frame(width: 340, height: 340)
            .clipShape(RoundedRectangle(cornerRadius: 6))
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color.secondary.opacity(0.3))
            )

            Text("116 mm printable disc  •  38 mm hub (non-printable)")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}

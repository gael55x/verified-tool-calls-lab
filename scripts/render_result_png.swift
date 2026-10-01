// Render a reviewed local SVG at its native 1700 x 885 size with macOS AppKit.
import AppKit
import Foundation

guard CommandLine.arguments.count == 3 else {
    fatalError("Usage: swift scripts/render_result_png.swift INPUT.svg OUTPUT.png")
}
let source = CommandLine.arguments[1]
let destination = CommandLine.arguments[2]
guard source.hasSuffix(".svg"), destination.hasSuffix(".png"),
      !FileManager.default.fileExists(atPath: destination),
      let image = NSImage(contentsOfFile: source),
      let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1700, pixelsHigh: 885,
                                    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                                    isPlanar: false, colorSpaceName: .deviceRGB,
                                    bytesPerRow: 0, bitsPerPixel: 0),
      let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fatalError("Input must be a readable SVG and output must not exist")
}
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
image.draw(in: NSRect(x: 0, y: 0, width: 1700, height: 885),
           from: .zero, operation: .copy, fraction: 1)
context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else {
    fatalError("PNG encoding failed")
}
try png.write(to: URL(fileURLWithPath: destination), options: .withoutOverwriting)

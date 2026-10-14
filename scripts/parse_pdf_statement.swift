import Foundation
import PDFKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("Usage: swift parse_pdf_statement.swift <pdf_path> [password] [output_path]")
    exit(1)
}

let path = args[1]
let password = args.count > 2 ? args[2] : ""
let outPath = args.count > 3 ? args[3] : "data/.statement_text.txt"

let url = URL(fileURLWithPath: path)
guard let doc = PDFDocument(url: url) else {
    print("Cannot open doc at \(path)")
    exit(1)
}

if doc.isEncrypted && !password.isEmpty {
    let unlocked = doc.unlock(withPassword: password)
    if !unlocked {
        print("Failed to unlock PDF with provided password")
        exit(1)
    }
}

var fullText = ""
for i in 0..<doc.pageCount {
    if let page = doc.page(at: i), let str = page.string {
        fullText += "\n=== PAGE \(i + 1) ===\n" + str
    }
}

try? fullText.write(toFile: outPath, atomically: true, encoding: .utf8)
print("Extracted \(doc.pageCount) pages to \(outPath)")

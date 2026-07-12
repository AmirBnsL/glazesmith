import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  if (process.env.NODE_ENV !== "development") {
    return new NextResponse("Not Found", { status: 404 });
  }

  try {
    const imagesDir = path.join(process.cwd(), "reference", "images");
    const files = fs.readdirSync(imagesDir);
    const jpgFiles = files.filter(f => f.toLowerCase().endsWith(".jpg"));

    if (jpgFiles.length === 0) {
      return new NextResponse("No images found", { status: 404 });
    }

    const randomFile = jpgFiles[Math.floor(Math.random() * jpgFiles.length)];
    const filePath = path.join(imagesDir, randomFile);
    const fileBuffer = fs.readFileSync(filePath);

    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "image/jpeg",
        "Cache-Control": "no-store, max-age=0",
      },
    });
  } catch (error) {
    console.error("Error reading random material:", error);
    return new NextResponse("Internal Server Error", { status: 500 });
  }
}

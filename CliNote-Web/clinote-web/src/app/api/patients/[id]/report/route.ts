import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ report: null });
}

export async function PUT() {
  return NextResponse.json({ message: "Update report" });
}

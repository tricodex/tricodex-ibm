import { NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData()
    
    const response = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      body: formData
    })
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to start analysis" },
      { status: 500 }
    )
  }
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const skip = searchParams.get('skip') || '0'
    const limit = searchParams.get('limit') || '10'
    
    const response = await fetch(`${API_URL}/projects?skip=${skip}&limit=${limit}`)
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    )
  }
}
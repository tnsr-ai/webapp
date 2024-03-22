import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const checkAccessToken = async (accessToken: string | undefined) => {
  if (accessToken === undefined) {
    return { status: false, verified: false };
  }
  const url: string = `${process.env.BASEURL}/auth/verify`;
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      credentials: "include",
    });
    if (response.status === 200) {
      const data = await response.json();
      return { status: true, verified: data?.data?.verified };
    }
    return { status: false, verified: false };
  } catch (error: any) {
    return { status: false, verified: false };
  }
};

const fetchAccessToken = async (refreshToken: string | undefined) => {
  if (refreshToken === undefined) {
    return false;
  }
  const url: string = `${process.env.BASEURL}/auth/refresh`;
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${refreshToken}`,
      },
      credentials: "include",
    });
    if (response.status != 200) {
      return false;
    }
    const data = await response.json();
    return data.data;
  } catch (error: any) {
    return false;
  }
};

// This function can be marked `async` if using `await` inside
export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get("access_token")?.value;
  const refreshToken = request.cookies.get("refreshToken")?.value;
  const nextResponse = NextResponse.next();
  const accessPublicPaths =
    request.nextUrl.pathname === "/" ||
    request.nextUrl.pathname === "/register" ||
    request.nextUrl.pathname === "/forgot-password";
  const verifiedOnlyPaths =
    request.nextUrl.pathname.includes("/video") ||
    request.nextUrl.pathname.includes("/audio") ||
    request.nextUrl.pathname.includes("/image") ||
    request.nextUrl.pathname.includes("/billing") ||
    request.nextUrl.pathname.includes("/jobs");
  const { status, verified } = await checkAccessToken(accessToken);
  if (accessPublicPaths) {
    if (status && verified) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    } else if (status && !verified) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    } else {
      return nextResponse;
    }
  } else {
    if (status === false) {
      const tokenData = await fetchAccessToken(refreshToken);
      if (tokenData === false) {
        return NextResponse.redirect(new URL("/", request.url));
      } else {
        nextResponse.cookies.set("access_token", tokenData.access_token, {
          maxAge: 30 * 60,
          secure: true,
          sameSite: "none",
          path: "/",
          domain: ".tnsr.ai",
          httpOnly: false,
        });
        nextResponse.cookies.set("refreshToken", tokenData.refreshToken, {
          maxAge: 30 * 60,
          secure: true,
          sameSite: "none",
          path: "/",
          domain: ".tnsr.ai",
          httpOnly: false,
        });
        return nextResponse;
      }
    } else if (status && !verified && verifiedOnlyPaths) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    } else if (status && !verified && !verifiedOnlyPaths) {
      return nextResponse;
    }
  }
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    "/",
    "/audio/:path*",
    "/video/:path*",
    "/image/:path*",
    "/billing/:path*",
    "/dashboard/:path*",
    "/jobs/:path*",
    "/settings/:path*",
    "/register/:path*",
    "/forgot-password/:path*",
  ],
};

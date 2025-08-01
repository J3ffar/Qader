import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { API_ENDPOINTS, API_BASE_URL, API_VERSION } from "@/constants/api";
import { REFRESH_TOKEN_COOKIE_NAME } from "@/constants/auth";
import { getLocaleFromPathname } from "@/utils/locale"; // Assuming this can work server-side or has a fallback

const DJANGO_API_URL = `${API_BASE_URL}/ar/api/${API_VERSION}`; // Using a default locale for server-to-server calls

// --- POST Handler for Login ---
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ action: string }> }
) {
  // We only support 'login' via POST
  // --- Login Logic (Unchanged but shown for context) ---
  if ((await params).action === "login") {
    try {
      const body = await req.json();
      const response = await fetch(
        `${DJANGO_API_URL}${API_ENDPOINTS.AUTH.LOGIN}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Cookie: req.headers.get("Cookie") ?? "",
          },
          body: JSON.stringify(body),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        return NextResponse.json(data, { status: response.status });
      }

      const responseToBrowser = NextResponse.json(data);

      response.headers.forEach((value, key) => {
        if (key.toLowerCase() === "set-cookie") {
          responseToBrowser.headers.append("Set-Cookie", value);
        }
      });

      const { access, refresh, user } = data;
      if (!refresh) {
        return NextResponse.json(
          { error: "Refresh token not provided" },
          { status: 500 }
        );
      }

      (await cookies()).set(REFRESH_TOKEN_COOKIE_NAME, refresh, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        path: "/",
        maxAge: 60 * 60 * 24 * 30, // 30 days
      });

      return responseToBrowser;
    } catch (error) {
      console.error("Login API route error:", error);
      return NextResponse.json(
        { error: "Internal Server Error" },
        { status: 500 }
      );
    }
  }

  // --- THE FIX: Add a new handler for 'confirm-email' ---
  if ((await params).action === "confirm-email") {
    try {
      const { uidb64, token } = await req.json();

      if (!uidb64 || !token) {
        return NextResponse.json(
          { error: "Missing confirmation parameters" },
          { status: 400 }
        );
      }

      // The Django endpoint is a GET request
      const response = await fetch(
        `${DJANGO_API_URL}${API_ENDPOINTS.AUTH.CONFIRM_EMAIL(uidb64, token)}`,
        { method: "GET" }
      );

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(data, { status: response.status });
      }

      const responseToBrowser = NextResponse.json(data);

      response.headers.forEach((value, key) => {
        if (key.toLowerCase() === "set-cookie") {
          responseToBrowser.headers.append("Set-Cookie", value);
        }
      });

      const { access, refresh, user } = data;
      if (!refresh) {
        return NextResponse.json(
          { error: "Refresh token not provided by backend on confirmation" },
          { status: 500 }
        );
      }

      // Securely set the refresh token in the HttpOnly cookie
      (await cookies()).set(REFRESH_TOKEN_COOKIE_NAME, refresh, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        path: "/",
        maxAge: 60 * 60 * 24 * 30, // 30 days
      });

      // Return only the access token and user data to the client
      return responseToBrowser;
    } catch (error) {
      console.error("Confirm Email API route error:", error);
      return NextResponse.json(
        { error: "Internal Server Error" },
        { status: 500 }
      );
    }
  }

  // Fallback for unsupported actions
  return NextResponse.json({ error: "Action not supported" }, { status: 404 });
}

// --- GET Handler for Logout and Session Hydration ('me') ---
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ action: string }> }
) {
  const action = (await params).action;

  // --- Logout Logic ---
  if (action === "logout") {
    (await cookies()).delete(REFRESH_TOKEN_COOKIE_NAME);
    return NextResponse.json({ message: "Logged out successfully" });
  }

  // --- Session Hydration Logic ---
  if (action === "me") {
    // Correctly await cookies().get()
    const refreshToken = (await cookies()).get(
      REFRESH_TOKEN_COOKIE_NAME
    )?.value;

    if (!refreshToken) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
      // 1. Get a new access token from Django using the refresh token
      const refreshResponse = await fetch(
        `${DJANGO_API_URL}${API_ENDPOINTS.AUTH.REFRESH_TOKEN}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: refreshToken }),
        }
      );

      const refreshData = await refreshResponse.json();
      if (!refreshResponse.ok) {
        // If refresh fails, the token is invalid. Log the user out.
        (await cookies()).delete(REFRESH_TOKEN_COOKIE_NAME);
        return NextResponse.json({ error: "Session expired" }, { status: 401 });
      }

      const { access: newAccessToken, refresh: newRefreshToken } = refreshData;

      // --- THE CRITICAL FIX FOR ROTATION ---
      // 2. Overwrite the cookie with the NEW refresh token from Django.
      if (newRefreshToken) {
        (await cookies()).set(REFRESH_TOKEN_COOKIE_NAME, newRefreshToken, {
          httpOnly: true,
          secure: process.env.NODE_ENV === "production",
          sameSite: "strict",
          path: "/",
          maxAge: 60 * 60 * 24 * 30, // Reset the expiration
        });
      }

      // 2. Use the new access token to get the current user's profile
      const userProfileResponse = await fetch(
        `${DJANGO_API_URL}${API_ENDPOINTS.USERS.ME}`,
        {
          headers: {
            Authorization: `Bearer ${newAccessToken}`,
          },
        }
      );

      const userData = await userProfileResponse.json();
      if (!userProfileResponse.ok) {
        return NextResponse.json(
          { error: "Failed to fetch user profile" },
          { status: 500 }
        );
      }

      // 3. Return the new access token and user data to the client
      return NextResponse.json({ access: newAccessToken, user: userData });
    } catch (error) {
      console.error("Session hydration ('me') API route error:", error);
      return NextResponse.json(
        { error: "Internal Server Error" },
        { status: 500 }
      );
    }
  }

  return NextResponse.json({ error: "Not Found" }, { status: 404 });
}

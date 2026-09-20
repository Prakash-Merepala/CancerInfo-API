import { initializeApp, getApps, getApp } from "firebase/app";
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  onAuthStateChanged,
  type User,
} from "firebase/auth";
import firebaseConfig from "../../firebase-applet-config.json";

// Initialize Firebase App once
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);

export const SCOPES = [
  "https://www.googleapis.com/auth/drive.readonly",
  "https://www.googleapis.com/auth/drive.file",
];

const provider = new GoogleAuthProvider();
SCOPES.forEach((scope) => {
  provider.addScope(scope);
});
provider.setCustomParameters({
  prompt: "consent",
  access_type: "online",
});

let isSigningIn = false;
let cachedAccessToken: string | null = null;

export const initAuth = (
  onAuthSuccess?: (user: User, token: string) => void,
  onAuthFailure?: () => void
) => {
  return onAuthStateChanged(auth, async (user: User | null) => {
    if (user) {
      if (cachedAccessToken) {
        if (onAuthSuccess) onAuthSuccess(user, cachedAccessToken);
      } else if (!isSigningIn) {
        cachedAccessToken = null;
        if (onAuthFailure) onAuthFailure();
      }
    } else {
      cachedAccessToken = null;
      if (onAuthFailure) onAuthFailure();
    }
  });
};

export const googleSignIn = async (): Promise<{ user: User; accessToken: string } | null> => {
  try {
    isSigningIn = true;
    const result = await signInWithPopup(auth, provider);
    const credential = GoogleAuthProvider.credentialFromResult(result);
    if (!credential?.accessToken) {
      throw new Error("Failed to get access token from Google sign-in.");
    }

    cachedAccessToken = credential.accessToken;
    return { user: result.user, accessToken: cachedAccessToken };
  } catch (error: any) {
    console.error("Google Drive Sign-in error:", error);
    throw error;
  } finally {
    isSigningIn = false;
  }
};

export const getAccessToken = async (): Promise<string | null> => {
  return cachedAccessToken;
};

export const logout = async () => {
  await auth.signOut();
  cachedAccessToken = null;
};

export interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  size?: string;
  modifiedTime?: string;
  webViewLink?: string;
  iconLink?: string;
  thumbnailLink?: string;
}

export interface DriveUserQuota {
  limit?: string;
  usage?: string;
  usageInDrive?: string;
}

/**
 * Lists files from the user's Google Drive.
 */
export async function listDriveFiles(
  token: string,
  options?: { query?: string; pageSize?: number }
): Promise<DriveFile[]> {
  const pageSize = options?.pageSize || 25;
  const fields = "files(id,name,mimeType,size,modifiedTime,webViewLink,iconLink,thumbnailLink)";
  
  let url = `https://www.googleapis.com/drive/v3/files?pageSize=${pageSize}&fields=${encodeURIComponent(
    fields
  )}&orderBy=modifiedTime desc`;

  if (options?.query) {
    const escapedQuery = options.query.replace(/'/g, "\\'");
    url += `&q=${encodeURIComponent(`name contains '${escapedQuery}' and trashed = false`)}`;
  } else {
    url += `&q=${encodeURIComponent("trashed = false")}`;
  }

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Google Drive API error (${res.status}): ${errorBody}`);
  }

  const data = await res.json();
  return (data.files as DriveFile[]) || [];
}

/**
 * Creates/uploads a text or JSON file (e.g. Cancer Info export) to Google Drive.
 */
export async function uploadFileToDrive(
  token: string,
  fileName: string,
  content: string,
  mimeType: string = "application/json"
): Promise<DriveFile> {
  const metadata = {
    name: fileName,
    mimeType: mimeType,
    description: "Saved from CancerInfo API Developer Portal",
  };

  const boundary = "-------314159265358979323846";
  const delimiter = `\r\n--${boundary}\r\n`;
  const closeDelimiter = `\r\n--${boundary}--`;

  const multipartRequestBody =
    delimiter +
    "Content-Type: application/json; charset=UTF-8\r\n\r\n" +
    JSON.stringify(metadata) +
    delimiter +
    `Content-Type: ${mimeType}\r\n\r\n` +
    content +
    closeDelimiter;

  const res = await fetch(
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,mimeType,webViewLink,modifiedTime",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": `multipart/related; boundary=${boundary}`,
      },
      body: multipartRequestBody,
    }
  );

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to upload to Google Drive (${res.status}): ${errorBody}`);
  }

  return (await res.json()) as DriveFile;
}

/**
 * Deletes a file from Google Drive.
 * Caller MUST confirm with user beforehand per skill guidelines.
 */
export async function deleteDriveFile(token: string, fileId: string): Promise<void> {
  const res = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok && res.status !== 204) {
    const errorBody = await res.text();
    throw new Error(`Failed to delete Google Drive file (${res.status}): ${errorBody}`);
  }
}

/**
 * Retrieves Drive about info / storage details.
 */
export async function getDriveAbout(token: string): Promise<{ user: any; storageQuota: DriveUserQuota }> {
  const res = await fetch("https://www.googleapis.com/drive/v3/about?fields=user,storageQuota", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch Drive about information: ${res.statusText}`);
  }

  return await res.json();
}

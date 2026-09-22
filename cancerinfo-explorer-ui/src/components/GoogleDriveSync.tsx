import React, { useState, useEffect } from "react";
import {
  initAuth,
  googleSignIn,
  logout,
  listDriveFiles,
  uploadFileToDrive,
  deleteDriveFile,
  getDriveAbout,
  type DriveFile,
  type DriveUserQuota,
  SCOPES,
} from "../services/googleDrive";
import type { User } from "firebase/auth";
import {
  FolderCheck,
  Search,
  RefreshCw,
  UploadCloud,
  FileText,
  ExternalLink,
  Trash2,
  CheckCircle2,
  AlertCircle,
  HardDrive,
  LogOut,
  Info,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

interface GoogleDriveSyncProps {
  currentEndpoint?: string;
  currentResponseJson?: string | null;
}

export const GoogleDriveSync: React.FC<GoogleDriveSyncProps> = ({
  currentEndpoint = "/v1/cancers/breast-cancer/symptoms",
  currentResponseJson = null,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [files, setFiles] = useState<DriveFile[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [quota, setQuota] = useState<DriveUserQuota | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  // Export state
  const [isExporting, setIsExporting] = useState(false);
  const [exportFileName, setExportFileName] = useState("cancerinfo-guidelines-export.json");
  const [lastUploadedFile, setLastUploadedFile] = useState<DriveFile | null>(null);

  // Deletion confirmation modal state
  const [fileToDelete, setFileToDelete] = useState<DriveFile | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const unsubscribe = initAuth(
      (authenticatedUser, accessToken) => {
        setUser(authenticatedUser);
        setToken(accessToken);
        fetchFilesAndQuota(accessToken);
      },
      () => {
        setUser(null);
        setToken(null);
        setFiles([]);
        setQuota(null);
      }
    );

    return () => {
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, []);

  const fetchFilesAndQuota = async (accessToken: string, query?: string) => {
    setIsLoadingFiles(true);
    try {
      const [driveFiles, about] = await Promise.all([
        listDriveFiles(accessToken, { query }),
        getDriveAbout(accessToken).catch(() => null),
      ]);
      setFiles(driveFiles);
      if (about?.storageQuota) {
        setQuota(about.storageQuota);
      }
    } catch (err: any) {
      console.error("Failed to load Google Drive files:", err);
      setStatusMessage({
        type: "error",
        text: `Error accessing Google Drive: ${err.message}`,
      });
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const handleSignIn = async () => {
    setIsLoggingIn(true);
    setStatusMessage(null);
    try {
      const result = await googleSignIn();
      if (result) {
        setUser(result.user);
        setToken(result.accessToken);
        setStatusMessage({
          type: "success",
          text: `Connected to Google Drive as ${result.user.email}`,
        });
        await fetchFilesAndQuota(result.accessToken);
      }
    } catch (err: any) {
      console.error("Login failed:", err);
      setStatusMessage({
        type: "error",
        text: `Sign-in failed: ${err.message || "Could not complete authorization"}`,
      });
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    setUser(null);
    setToken(null);
    setFiles([]);
    setQuota(null);
    setStatusMessage({
      type: "info",
      text: "Disconnected from Google Drive.",
    });
  };

  const handleExportToDrive = async () => {
    if (!token) return;
    setIsExporting(true);
    setStatusMessage(null);
    try {
      const contentToUpload =
        currentResponseJson ||
        JSON.stringify(
          {
            exported_at: new Date().toISOString(),
            source: "CancerInfo API Developer Portal",
            endpoint: currentEndpoint,
            disclaimer: "Informational clinical summary only; not medical advice.",
          },
          null,
          2
        );

      const uploaded = await uploadFileToDrive(token, exportFileName, contentToUpload, "application/json");
      setLastUploadedFile(uploaded);
      setStatusMessage({
        type: "success",
        text: `Successfully exported '${uploaded.name}' to your Google Drive!`,
      });
      // Refresh list
      await fetchFilesAndQuota(token, searchQuery);
    } catch (err: any) {
      console.error("Export failed:", err);
      setStatusMessage({
        type: "error",
        text: `Export failed: ${err.message}`,
      });
    } finally {
      setIsExporting(false);
    }
  };

  const confirmDeleteFile = async () => {
    if (!token || !fileToDelete) return;
    setIsDeleting(true);
    try {
      await deleteDriveFile(token, fileToDelete.id);
      setStatusMessage({
        type: "success",
        text: `Deleted '${fileToDelete.name}' from Google Drive.`,
      });
      setFileToDelete(null);
      await fetchFilesAndQuota(token, searchQuery);
    } catch (err: any) {
      console.error("Delete failed:", err);
      setStatusMessage({
        type: "error",
        text: `Failed to delete file: ${err.message}`,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytesStr?: string) => {
    if (!bytesStr) return "--";
    const bytes = parseInt(bytesStr, 10);
    if (isNaN(bytes)) return "--";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & OAuth Connection State */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-sky-700 flex items-center justify-center text-white shadow-md shadow-blue-500/20 flex-shrink-0">
              <HardDrive className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white tracking-tight">Google Drive Integration</h3>
                {user ? (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Connected</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
                    <span>Not Connected</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
                Connect your Google Drive account to seamlessly view files, export authoritative cancer guidelines,
                and back up clinical research queries with OAuth verification.
              </p>
            </div>
          </div>

          <div>
            {!user ? (
              /* Google Standard Sign-in Button adhering to skill design */
              <button
                id="google-drive-signin-button"
                onClick={handleSignIn}
                disabled={isLoggingIn}
                className="inline-flex items-center space-x-3 px-5 py-2.5 rounded-lg bg-white hover:bg-slate-100 text-slate-800 font-semibold text-sm shadow-md transition disabled:opacity-60 cursor-pointer"
              >
                {isLoggingIn ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-slate-700" />
                ) : (
                  <svg className="w-5 h-5" viewBox="0 0 48 48">
                    <path
                      fill="#EA4335"
                      d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
                    />
                    <path
                      fill="#4285F4"
                      d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
                    />
                    <path
                      fill="#34A853"
                      d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
                    />
                  </svg>
                )}
                <span>{isLoggingIn ? "Authorizing Google Drive..." : "Sign in with Google"}</span>
              </button>
            ) : (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
                  {user.photoURL ? (
                    <img src={user.photoURL} alt={user.displayName || "User"} className="w-6 h-6 rounded-full" />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-sky-600 text-xs flex items-center justify-center font-bold">
                      {user.email?.charAt(0).toUpperCase() || "U"}
                    </div>
                  )}
                  <div className="text-left">
                    <p className="text-xs font-medium text-white leading-none">{user.displayName || "Google User"}</p>
                    <p className="text-[10px] text-slate-400 leading-tight mt-0.5">{user.email}</p>
                  </div>
                </div>

                <button
                  onClick={handleSignOut}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-rose-900/40 text-slate-300 hover:text-rose-300 border border-slate-700 hover:border-rose-800 transition text-xs"
                  title="Disconnect Google Drive"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Granted Scopes Badge Details */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center space-x-1 text-slate-300 font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
            <span>Active OAuth Scopes:</span>
          </span>
          {SCOPES.map((s) => (
            <span
              key={s}
              className="px-2 py-0.5 rounded bg-slate-800 font-mono text-[11px] text-sky-300 border border-slate-700"
            >
              {s.replace("https://www.googleapis.com/auth/", "")}
            </span>
          ))}
          {quota && quota.usage && quota.limit && (
            <span className="ml-auto text-[11px] text-slate-400 font-mono">
              Drive Usage: {formatFileSize(quota.usage)} / {formatFileSize(quota.limit)}
            </span>
          )}
        </div>
      </div>

      {/* Notification Banner */}
      {statusMessage && (
        <div
          className={`px-4 py-3 rounded-lg text-xs font-medium flex items-center space-x-2 border ${
            statusMessage.type === "success"
              ? "bg-emerald-950/60 text-emerald-300 border-emerald-800"
              : statusMessage.type === "error"
              ? "bg-rose-950/60 text-rose-300 border-rose-800"
              : "bg-sky-950/60 text-sky-300 border-sky-800"
          }`}
        >
          {statusMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* When Authenticated: Export Panel & File Browser */}
      {user && token ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Quick Export to Drive */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center space-x-2">
                <UploadCloud className="w-4 h-4 text-sky-400" />
                <h4 className="text-sm font-semibold text-white">Save API Data to Drive</h4>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Save the currently selected CancerInfo API response or clinical guidelines report directly into your
                Google Drive as a structured JSON file.
              </p>

              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-300">File Name</label>
                <input
                  type="text"
                  value={exportFileName}
                  onChange={(e) => setExportFileName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-xs font-mono text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                <div className="text-[11px] text-slate-400">Target Endpoint:</div>
                <div className="text-xs font-mono text-sky-400 break-all">{currentEndpoint}</div>
              </div>

              <button
                id="export-to-drive-btn"
                onClick={handleExportToDrive}
                disabled={isExporting}
                className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50 cursor-pointer"
              >
                {isExporting ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <UploadCloud className="w-3.5 h-3.5" />
                )}
                <span>{isExporting ? "Uploading to Drive..." : "Export to My Google Drive"}</span>
              </button>

              {lastUploadedFile && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/80 space-y-2">
                  <div className="flex items-center space-x-1.5 text-xs font-medium text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>File saved successfully</span>
                  </div>
                  <p className="text-xs text-slate-300 font-mono truncate">{lastUploadedFile.name}</p>
                  {lastUploadedFile.webViewLink && (
                    <a
                      href={lastUploadedFile.webViewLink}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1 text-xs text-sky-400 hover:underline"
                    >
                      <span>Open in Google Drive</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              )}
            </div>

            {/* Integration Tip Card */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-2">
              <div className="flex items-center space-x-1.5 text-slate-200 font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Privacy & Token Security</span>
              </div>
              <p className="leading-relaxed">
                OAuth access tokens are held strictly in memory and are never persisted to localStorage or sent to any
                third party. Tokens expire automatically upon sign-out.
              </p>
            </div>
          </div>

          {/* Right Column: Google Drive File Explorer */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                <FolderCheck className="w-4 h-4 text-sky-400" />
                <h4 className="text-sm font-semibold text-white">Your Google Drive Files</h4>
                <span className="text-xs font-mono text-slate-400">({files.length} loaded)</span>
              </div>

              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search Drive files..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && fetchFilesAndQuota(token, searchQuery)}
                    className="pl-8 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 w-44 sm:w-56"
                  />
                </div>

                <button
                  onClick={() => fetchFilesAndQuota(token, searchQuery)}
                  disabled={isLoadingFiles}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                  title="Refresh Drive Files"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isLoadingFiles ? "animate-spin" : ""}`} />
                </button>
              </div>
            </div>

            {/* Files Table / List */}
            {isLoadingFiles ? (
              <div className="py-12 text-center text-slate-400 space-y-2">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-sky-400" />
                <p className="text-xs">Loading files from your Google Drive...</p>
              </div>
            ) : files.length === 0 ? (
              <div className="py-12 text-center border border-dashed border-slate-800 rounded-lg text-slate-400 space-y-2">
                <FileText className="w-8 h-8 mx-auto text-slate-600" />
                <p className="text-xs font-medium text-slate-300">No files found</p>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  {searchQuery ? `No files matching '${searchQuery}'` : "Your Drive does not have any accessible files yet, or you can export guidelines above."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase text-[10px] tracking-wider font-semibold">
                    <tr>
                      <th className="px-4 py-3">File Name</th>
                      <th className="px-3 py-3">Type</th>
                      <th className="px-3 py-3">Size</th>
                      <th className="px-3 py-3">Last Modified</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {files.map((file) => (
                      <tr key={file.id} className="hover:bg-slate-800/40 transition">
                        <td className="px-4 py-3">
                          <div className="flex items-center space-x-2">
                            {file.iconLink ? (
                              <img src={file.iconLink} alt="" className="w-4 h-4 flex-shrink-0" />
                            ) : (
                              <FileText className="w-4 h-4 text-sky-400 flex-shrink-0" />
                            )}
                            <span className="font-medium text-white truncate max-w-xs" title={file.name}>
                              {file.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-3 py-3 font-mono text-[11px] text-slate-400 truncate max-w-[120px]">
                          {file.mimeType.split("/").pop()}
                        </td>
                        <td className="px-3 py-3 font-mono text-[11px] text-slate-400">
                          {formatFileSize(file.size)}
                        </td>
                        <td className="px-3 py-3 text-[11px] text-slate-400">
                          {file.modifiedTime ? new Date(file.modifiedTime).toLocaleDateString() : "--"}
                        </td>
                        <td className="px-4 py-3 text-right space-x-2">
                          {file.webViewLink && (
                            <a
                              href={file.webViewLink}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center p-1.5 rounded hover:bg-slate-700 text-slate-300 hover:text-white transition"
                              title="Open in Google Drive"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                          <button
                            onClick={() => setFileToDelete(file)}
                            className="inline-flex items-center p-1.5 rounded hover:bg-rose-950/80 text-slate-400 hover:text-rose-400 transition cursor-pointer"
                            title="Delete file"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Not Authenticated State Card */
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-blue-950/60 border border-blue-800/80 flex items-center justify-center mx-auto text-blue-400 shadow-inner">
            <FolderCheck className="w-7 h-7" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h4 className="text-base font-semibold text-white">Connect Google Drive to Get Started</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Authenticate via the button above to enable reading your Google Drive files and archiving live
              CancerInfo clinical guidelines and queries to your cloud storage.
            </p>
          </div>
          <div className="pt-2">
            <button
              onClick={handleSignIn}
              disabled={isLoggingIn}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition shadow-md cursor-pointer"
            >
              {isLoggingIn ? <RefreshCw className="w-4 h-4 animate-spin" /> : <HardDrive className="w-4 h-4" />}
              <span>{isLoggingIn ? "Authorizing..." : "Connect Google Drive Now"}</span>
            </button>
          </div>
        </div>
      )}

      {/* MANDATORY Confirmation Modal for Destructive Operations */}
      {fileToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 rounded-lg bg-rose-950/80 border border-rose-800 flex items-center justify-center text-rose-400 flex-shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-white">Delete File from Google Drive?</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Are you sure you want to permanently delete{" "}
                  <span className="font-semibold text-white font-mono">"{fileToDelete.name}"</span>? This operation
                  will remove the file from your Google Drive.
                </p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
              <div>
                File ID: <span className="font-mono text-slate-300">{fileToDelete.id}</span>
              </div>
              <div>
                Type: <span className="font-mono text-slate-300">{fileToDelete.mimeType}</span>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setFileToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDeleteFile}
                disabled={isDeleting}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition disabled:opacity-50 cursor-pointer"
              >
                {isDeleting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>{isDeleting ? "Deleting..." : "Confirm & Delete File"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

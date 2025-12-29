/**
 * Bulk User Upload View
 * Custom FireCMS view for mass user creation via CSV
 * Per TRD: Mass CSV user upload is critical for district onboarding
 */

import React, { useState, useCallback } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import DownloadIcon from "@mui/icons-material/Download";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";

import {
  parseCSV,
  generateCSVTemplate,
  processBulkUpload,
  validateCSV,
  BulkUserData,
  BulkUploadResult,
} from "../actions/bulkUserUpload";

interface BulkUserUploadViewProps {
  firebaseApp?: any;
}

export function BulkUserUploadView({ firebaseApp }: BulkUserUploadViewProps) {
  const [csvContent, setCSVContent] = useState("");
  const [parsedUsers, setParsedUsers] = useState<BulkUserData[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadResult, setUploadResult] = useState<BulkUploadResult | null>(null);

  // Handle file upload
  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setCSVContent(content);
      handleValidate(content);
    };
    reader.readAsText(file);
  }, []);

  // Validate CSV
  const handleValidate = useCallback((content: string) => {
    setValidationError(null);
    setParsedUsers([]);
    setUploadResult(null);

    if (!content.trim()) {
      return;
    }

    const validation = validateCSV(content);
    if (!validation.valid) {
      setValidationError(validation.error || "Invalid CSV format");
      return;
    }

    try {
      const users = parseCSV(content);
      setParsedUsers(users);
    } catch (error: any) {
      setValidationError(error.message);
    }
  }, []);

  // Process upload
  const handleUpload = useCallback(async () => {
    if (parsedUsers.length === 0 || !firebaseApp) return;

    setIsProcessing(true);
    setUploadResult(null);

    try {
      const result = await processBulkUpload(parsedUsers, firebaseApp);
      setUploadResult(result);
    } catch (error: any) {
      setValidationError(`Upload failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  }, [parsedUsers, firebaseApp]);

  // Download template
  const handleDownloadTemplate = useCallback(() => {
    const template = generateCSVTemplate();
    const blob = new Blob([template], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "user_upload_template.csv";
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  return (
    <Box sx={{ p: 3, maxWidth: 1200, margin: "0 auto" }}>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, color: "#1f2937" }}>
        Bulk User Upload
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Upload a CSV file to create multiple user accounts at once. This is ideal for
        district onboarding.
      </Typography>

      {/* Template Download */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Step 1: Download Template
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Download the CSV template with the required columns and format
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
            >
              Download Template
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* File Upload */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Step 2: Upload CSV File
          </Typography>
          
          <Box
            sx={{
              border: "2px dashed #e5e7eb",
              borderRadius: 2,
              p: 4,
              textAlign: "center",
              bgcolor: "#f9fafb",
              cursor: "pointer",
              "&:hover": { borderColor: "#ef4444", bgcolor: "#fef2f2" },
            }}
            component="label"
          >
            <input
              type="file"
              accept=".csv"
              hidden
              onChange={handleFileUpload}
            />
            <CloudUploadIcon sx={{ fontSize: 48, color: "#9ca3af", mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              Click to upload or drag and drop
            </Typography>
            <Typography variant="caption" color="text.secondary">
              CSV file up to 1000 users
            </Typography>
          </Box>

          {/* Or paste CSV */}
          <Typography variant="body2" sx={{ my: 2, textAlign: "center", color: "#6b7280" }}>
            — or paste CSV content directly —
          </Typography>

          <TextField
            fullWidth
            multiline
            rows={6}
            placeholder="email,displayName,role,districtId,schoolName&#10;teacher@school.com,John Smith,teacher,district-123,Lincoln Elementary"
            value={csvContent}
            onChange={(e) => {
              setCSVContent(e.target.value);
              handleValidate(e.target.value);
            }}
            sx={{ fontFamily: "monospace" }}
          />
        </CardContent>
      </Card>

      {/* Validation Error */}
      {validationError && (
        <Alert severity="error" sx={{ mb: 3 }} icon={<ErrorIcon />}>
          {validationError}
        </Alert>
      )}

      {/* Preview */}
      {parsedUsers.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Step 3: Review Users ({parsedUsers.length} found)
            </Typography>

            <Paper sx={{ maxHeight: 400, overflow: "auto" }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Display Name</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>District</TableCell>
                    <TableCell>School</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parsedUsers.slice(0, 50).map((user, index) => (
                    <TableRow key={index}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>{user.displayName}</TableCell>
                      <TableCell>
                        <Chip
                          label={user.role}
                          size="small"
                          color={
                            user.role === "admin"
                              ? "error"
                              : user.role === "content_manager"
                              ? "warning"
                              : "default"
                          }
                        />
                      </TableCell>
                      <TableCell>{user.districtId || "-"}</TableCell>
                      <TableCell>{user.schoolName || "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>

            {parsedUsers.length > 50 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
                Showing first 50 of {parsedUsers.length} users
              </Typography>
            )}

            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleUpload}
                disabled={isProcessing}
                startIcon={<CloudUploadIcon />}
                sx={{ bgcolor: "#ef4444", "&:hover": { bgcolor: "#dc2626" } }}
              >
                {isProcessing ? "Processing..." : `Create ${parsedUsers.length} Users`}
              </Button>
            </Box>

            {isProcessing && <LinearProgress sx={{ mt: 2 }} />}
          </CardContent>
        </Card>
      )}

      {/* Upload Result */}
      {uploadResult && (
        <Alert
          severity={uploadResult.success ? "success" : "warning"}
          icon={uploadResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
          sx={{ mb: 3 }}
        >
          <Typography variant="subtitle1" fontWeight={600}>
            Upload Complete
          </Typography>
          <Typography variant="body2">
            Successfully created: {uploadResult.successCount} / {uploadResult.totalProcessed} users
          </Typography>
          {uploadResult.failedCount > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="error">
                Failed ({uploadResult.failedCount}):
              </Typography>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {uploadResult.errors.slice(0, 10).map((err, i) => (
                  <li key={i}>
                    <Typography variant="caption">
                      {err.email}: {err.error}
                    </Typography>
                  </li>
                ))}
              </ul>
            </Box>
          )}
        </Alert>
      )}

      {/* Instructions */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            CSV Format Guide
          </Typography>
          <Typography variant="body2" color="text.secondary" component="div">
            <strong>Required columns:</strong>
            <ul>
              <li><code>email</code> - User's email address (must be unique)</li>
              <li><code>displayName</code> - User's display name</li>
            </ul>
            <strong>Optional columns:</strong>
            <ul>
              <li><code>role</code> - admin, content_manager, or teacher (default: teacher)</li>
              <li><code>districtId</code> - District identifier</li>
              <li><code>schoolName</code> - School name</li>
            </ul>
            <strong>Notes:</strong>
            <ul>
              <li>Maximum 1000 users per upload</li>
              <li>Users will receive email invitations to set their password</li>
              <li>Duplicate emails will be skipped</li>
            </ul>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default BulkUserUploadView;


# Step 8: Firebase Storage Lifecycle Rules (Cost Optimization)

## 🎯 Overview
Storage Lifecycle Rules automatically manage your files to reduce costs by:
- Moving old files to cheaper storage classes
- Deleting unused files automatically
- Optimizing storage costs without manual intervention

## 💰 Cost Savings Potential
- **Standard Storage:** $0.020/GB/month
- **Nearline Storage:** $0.010/GB/month (accessed < once/month)
- **Coldline Storage:** $0.004/GB/month (accessed < once/quarter)
- **Archive Storage:** $0.0012/GB/month (accessed < once/year)

---

## 📋 STEP-BY-STEP INSTRUCTIONS

### Step 8.1: Access Google Cloud Console
**Why Google Cloud Console?** Firebase Storage lifecycle rules are managed through Google Cloud Console, not Firebase Console.

1. **Go to:** [Google Cloud Console](https://console.cloud.google.com/)
2. **Select your project:** `fractionball-lms`
3. **Navigate to:** Storage → Buckets

### Step 8.2: Find Your Firebase Storage Bucket
1. **Look for bucket named:** `fractionball-lms.appspot.com` or similar
2. **Click on the bucket name** to open it
3. **Click on the "Lifecycle" tab** at the top

### Step 8.3: Create Lifecycle Rules

#### Rule 1: Move Videos to Coldline Storage (Cost Savings)
**Purpose:** Videos are typically watched once, then rarely accessed again.

1. **Click "Add Rule"**
2. **Rule Configuration:**
   - **Action:** "Set storage class to Coldline"
   - **Conditions:**
     - **Age:** 30 days
     - **Object name prefix:** `videos/`
   - **Description:** "Move videos to coldline after 30 days"
3. **Click "Create"**

#### Rule 2: Move Resources to Nearline Storage
**Purpose:** Resources may be downloaded occasionally but not frequently.

1. **Click "Add Rule"**
2. **Rule Configuration:**
   - **Action:** "Set storage class to Nearline"
   - **Conditions:**
     - **Age:** 60 days
     - **Object name prefix:** `resources/`
   - **Description:** "Move resources to nearline after 60 days"
3. **Click "Create"**

#### Rule 3: Delete Orphaned Uploads (Cleanup)
**Purpose:** Remove incomplete or failed uploads that aren't referenced in your database.

1. **Click "Add Rule"**
2. **Rule Configuration:**
   - **Action:** "Delete object"
   - **Conditions:**
     - **Age:** 7 days
     - **Object name prefix:** `temp/` (for temporary uploads)
   - **Description:** "Delete temporary files after 7 days"
3. **Click "Create"**

#### Rule 4: Archive Old Thumbnails
**Purpose:** Thumbnails are rarely accessed after initial viewing.

1. **Click "Add Rule"**
2. **Rule Configuration:**
   - **Action:** "Set storage class to Archive"
   - **Conditions:**
     - **Age:** 90 days
     - **Object name prefix:** `thumbnails/`
   - **Description:** "Archive thumbnails after 90 days"
3. **Click "Create"**

### Step 8.4: Advanced Rule (Optional) - Delete Very Old Content
**⚠️ CAUTION:** Only implement this if you have a data retention policy.

1. **Click "Add Rule"**
2. **Rule Configuration:**
   - **Action:** "Delete object"
   - **Conditions:**
     - **Age:** 1095 days (3 years)
     - **Object name prefix:** `videos/`
   - **Description:** "Delete videos older than 3 years"
3. **Click "Create"**

---

## 🔧 ALTERNATIVE: Lifecycle Rules via gsutil (Command Line)

If you prefer command line, you can set up lifecycle rules using gsutil:

### Install Google Cloud SDK (if not installed)
```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### Create Lifecycle Configuration File
```bash
cat > lifecycle-config.json << 'LIFECYCLE_EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "COLDLINE"
        },
        "condition": {
          "age": 30,
          "matchesPrefix": ["videos/"]
        }
      },
      {
        "action": {
          "type": "SetStorageClass", 
          "storageClass": "NEARLINE"
        },
        "condition": {
          "age": 60,
          "matchesPrefix": ["resources/"]
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 7,
          "matchesPrefix": ["temp/"]
        }
      },
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "ARCHIVE"
        },
        "condition": {
          "age": 90,
          "matchesPrefix": ["thumbnails/"]
        }
      }
    ]
  }
}
LIFECYCLE_EOF
```

### Apply Lifecycle Rules
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project fractionball-lms

# Apply lifecycle rules to your bucket
gsutil lifecycle set lifecycle-config.json gs://fractionball-lms.appspot.com
```

---

## 📊 COST IMPACT ANALYSIS

### Example Monthly Costs (1TB of content):

**Without Lifecycle Rules:**
- 1TB Standard Storage: $20.48/month

**With Lifecycle Rules:**
- 100GB Standard (recent): $2.05/month
- 400GB Nearline (resources): $4.10/month  
- 400GB Coldline (videos): $1.64/month
- 100GB Archive (old thumbnails): $0.12/month
- **Total: $7.91/month (61% savings!)**

---

## ✅ VERIFICATION STEPS

### Step 8.5: Verify Rules Are Active
1. **Go back to:** Google Cloud Console → Storage → Buckets
2. **Click your bucket** → **Lifecycle tab**
3. **Verify all rules are listed** and active
4. **Check rule order** (rules are processed in order)

### Step 8.6: Test with Sample Files (Optional)
1. **Upload a test file** to each folder
2. **Wait for rules to take effect** (may take 24-48 hours)
3. **Check storage class changes** in the bucket browser

---

## 🚨 IMPORTANT CONSIDERATIONS

### Data Access Patterns
- **Coldline:** Retrieval costs apply ($0.01/GB)
- **Archive:** Higher retrieval costs ($0.05/GB) + minimum 365-day storage
- **Plan accordingly** based on your app's usage patterns

### Rule Interactions
- Rules are **processed in order**
- **First matching rule wins**
- Test with small amounts first

### Monitoring
- Set up **billing alerts** in Google Cloud Console
- Monitor **storage class distribution**
- Track **retrieval costs**

---

## 🎯 NEXT STEPS AFTER STEP 8

1. **Monitor costs** for 1-2 months
2. **Adjust rules** based on actual usage patterns
3. **Set up billing alerts** in Google Cloud Console
4. **Continue to Step 9:** Monitoring and Alerts

---

## 📞 TROUBLESHOOTING

**Rules not applying?**
- Wait 24-48 hours for rules to take effect
- Check rule conditions and syntax
- Verify bucket permissions

**Unexpected costs?**
- Check retrieval charges for coldline/archive
- Monitor egress bandwidth costs
- Review rule conditions

**Need to modify rules?**
- Edit existing rules in Google Cloud Console
- Test changes with small file sets first
- Monitor cost impact

---

**Created for:** Fraction Ball LMS Firebase Setup
**Estimated Monthly Savings:** 50-70% on storage costs
**Implementation Time:** 15-30 minutes

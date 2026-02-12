import os
import glob
import logging

# Setup logging for a professional feel
logging.basicConfig(level=logging.INFO, format='%(message)s')

def smart_ssh_cleanup():
    """
    Cleans up SSH junk files using pattern matching while protecting critical identity keys.
    Author: Software Engineer Chatbot (Gemini)
    """
    ssh_path = os.path.expanduser("~/.ssh/")
    
    print("🚀 Starting Professional SSH Environment Cleanup...")
    print("-" * 60)

    # 1. DEFINE PROTECTED FILES (The Safety Guard)
    # These files are core identities. We explicitly exclude them from any deletion logic.
    protected_files = {
        os.path.join(ssh_path, "id_ed25519"),
        os.path.join(ssh_path, "id_ed25519.pub"),
        os.path.join(ssh_path, "authorized_keys")
    }

    # 2. DEFINE CLEANUP TARGETS (Pattern Matching)
    # We use wildcards to catch all variations of temporary/backup files
    cleanup_patterns = ["*.old", "*.tmp", "*.bak", "known_hosts"]
    
    files_to_clean = []
    for pattern in cleanup_patterns:
        full_pattern = os.path.join(ssh_path, pattern)
        files_to_clean.extend(glob.glob(full_pattern))

    # 3. EXECUTION PHASE WITH SAFETY FILTERS
    cleaned_count = 0
    for file_path in files_to_clean:
        # Safety Check: Skip if the file is in our protected set
        if file_path in protected_files:
            continue
            
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {os.path.basename(file_path)}")
                cleaned_count += 1
            except OSError as e:
                print(f"❌ Error removing {os.path.basename(file_path)}: {e.strerror}")

    # 4. IDENTITY INTEGRITY VERIFICATION
    print("\n🔐 Verifying SSH Identity Keys:")
    for key_file in sorted(list(protected_files)):
        if os.path.exists(key_file):
            print(f"✔️  [SAFE] {os.path.basename(key_file)} is preserved.")
        else:
            # We don't error out if they don't exist, we just inform
            print(f"ℹ️  [INFO] {os.path.basename(key_file)} is not present (Skipping).")

    # 5. RE-INITIALIZE KNOWN_HOSTS (Secure Reset)
    try:
        hosts_path = os.path.join(ssh_path, "known_hosts")
        # Creating a fresh file with correct permissions (chmod 600)
        with open(hosts_path, "w") as f:
            pass 
        os.chmod(hosts_path, 0o600)
        print("\n🆕 'known_hosts' has been securely reset.")
    except Exception as e:
        print(f"❌ Failed to reset known_hosts: {e}")
    
    print("-" * 60)
    print(f"✨ Cleanup Complete! Total junk files removed: {cleaned_count}")
    print("🚀 Your SSH directory is now clean and optimized.")

if __name__ == "__main__":
    smart_ssh_cleanup()

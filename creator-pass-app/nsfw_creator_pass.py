"""
NSFW-Powered Universal Creator Pass - Consolidated Application
A cross-platform membership layer for NSFW content with blockchain integration
"""

# ============================================================================
# SECTION 1: IMPORTS
# ============================================================================
import streamlit as st
import hashlib
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ============================================================================
# SECTION 2: CONFIGURATION
# ============================================================================
class Config:
    """Application configuration - replace with your actual values"""
    
    # Blockchain RPC URLs (from APIs.txt)
    ETHEREUM_RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/MQbXzyHgvG3O6LkgC9rco"
    ETHEREUM_FALLBACK_RPC_URL = "https://mainnet.infura.io/v3/71a8bf00395d4ca2961b0990df8594a4"
    POLYGON_RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/71a8bf00395d4ca2961b0990df8594a4"
    
    # Etherscan API
    ETHERSCAN_API_KEY = "UP4GZ8UFZT6RDBQAMY7UGYRIWR2BH9YV8X"
    
    # Security
    SECRET_KEY = "bat-h5h68h-t8s0s9-g98g9g-5j1j2j-9n0mt0-0s-y4u4r-5k6k4-5y7ur8-2e3r4t5"
    
    # Contract Addresses (replace with actual contract addresses)
    CREATOR_PASS_CONTRACT = "0x0000000000000000000000000000000000000000"  # Placeholder
    CREATOR_PASS_CONTRACT_POLYGON = "0x0000000000000000000000000000000000000000"  # Placeholder
    
    # Database
    DATABASE_URL = "sqlite:///creator_pass.db"
    
    # Directories
    IMAGES_DIR = "images"
    UPLOADS_DIR = "uploads"

# ============================================================================
# SECTION 3: DATABASE MODELS
# ============================================================================
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True)
    username = Column(String(50))
    email = Column(String(100))
    bio = Column(Text)
    profile_image = Column(String(255))
    nsfw_enabled = Column(Boolean, default=False)
    membership_tier = Column(String(20), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class CreatorPass(Base):
    __tablename__ = "creator_passes"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, unique=True)
    owner_address = Column(String(42))
    contract_address = Column(String(42))
    network = Column(String(20))  # ethereum, polygon, etc.
    tier = Column(String(20))  # basic, premium, vip
    expires_at = Column(DateTime)
    metadata_uri = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class NSFWContent(Base):
    __tablename__ = "nsfw_content"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer)
    content_hash = Column(String(66))  # IPFS hash
    title = Column(String(200))
    description = Column(Text)
    category = Column(String(50))
    is_exclusive = Column(Boolean, default=False)
    price_eth = Column(String(20))
    price_matic = Column(String(20))
    nsfw_level = Column(String(20))
    file_path = Column(String(500))  # Path to local file
    created_at = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=False)

# Initialize database
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# Create directories if they don't exist
os.makedirs(Config.IMAGES_DIR, exist_ok=True)
os.makedirs(Config.UPLOADS_DIR, exist_ok=True)

# ============================================================================
# SECTION 4: UTILITY FUNCTIONS
# ============================================================================
def format_eth_address(address):
    """Format Ethereum address for display"""
    if address and len(address) > 10:
        return f"{address[:6]}...{address[-4:]}"
    return address

def get_local_images():
    """Load images from local images/ directory"""
    image_dir = Path(Config.IMAGES_DIR)
    local_images = []
    
    if image_dir.exists():
        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        for ext in image_extensions:
            for img_path in image_dir.glob(f"*{ext}"):
                # Store relative path
                rel_path = f"{Config.IMAGES_DIR}/{img_path.name}"
                local_images.append({
                    "img": rel_path,
                    "title": img_path.stem.replace("_", " ").title(),
                    "price": "0.1 ETH",  # Default price
                    "is_local": True
                })
    
    return local_images

def save_uploaded_file(uploaded_file, filename=None):
    """Save uploaded file to uploads directory"""
    if filename is None:
        filename = uploaded_file.name
    
    # Create safe filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()
    
    # Save file
    file_path = os.path.join(Config.UPLOADS_DIR, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

# ============================================================================
# SECTION 5: STREAMLIT APPLICATION
# ============================================================================
def main():
    # Page configuration
    st.set_page_config(
        page_title="NSFW Creator Pass",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS (same as before, but add CSS for local image display)
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF6B6B;
            text-align: center;
            margin-bottom: 2rem;
        }
        .wallet-address {
            background-color: #2E2E2E;
            padding: 10px;
            border-radius: 10px;
            font-family: monospace;
            color: #4ECDC4;
        }
        .membership-badge {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            font-weight: bold;
        }
        .nsfw-warning {
            background-color: #FF6B6B;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }
        .gallery {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-start;
            gap: 20px;
            margin-top: 20px;
        }
        .gallery-item {
            width: 180px;
            border: 1px solid #ccc;
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s;
        }
        .gallery-item:hover {
            transform: scale(1.05);
            border-color: #FF6B6B;
        }
        .gallery-item img {
            width: 100%;
            height: 180px;
            object-fit: cover;
        }
        .gallery-item .desc {
            padding: 10px;
            text-align: center;
            background: #2E2E2E;
            color: white;
        }
        .gallery-item .price {
            color: #4ECDC4;
            font-weight: bold;
            font-size: 0.9rem;
        }
        .local-badge {
            position: absolute;
            top: 5px;
            right: 5px;
            background: #4ECDC4;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "Home"
    if 'wallet_address' not in st.session_state:
        st.session_state.wallet_address = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'is_member' not in st.session_state:
        st.session_state.is_member = False
    
    # Sidebar (same as before)
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150/FF6B6B/FFFFFF?text=NSFW+Pass", width=150)
        st.markdown("## 🔐 Universal Creator Pass")
        
        # Wallet connection
        st.markdown("### Connect Wallet")
        wallet_address = st.text_input("Enter Wallet Address", placeholder="0x...", key="wallet_input")
        
        if st.button("Connect", type="primary", key="connect_btn"):
            if wallet_address and len(wallet_address) == 42:
                st.session_state.wallet_address = wallet_address
                st.session_state.is_member = wallet_address.lower().endswith('a')
                st.success("Wallet connected!")
            else:
                st.error("Please enter a valid wallet address (42 characters)")
        
        if st.session_state.wallet_address:
            st.markdown("**Connected:**")
            st.markdown(f'<div class="wallet-address">{format_eth_address(st.session_state.wallet_address)}</div>', 
                       unsafe_allow_html=True)
            
            if st.session_state.is_member:
                st.markdown('<div class="membership-badge">🎫 Premium Member</div>', 
                           unsafe_allow_html=True)
            else:
                st.warning("No active membership")
        
        # Navigation
        st.markdown("---")
        st.markdown("### Navigation")
        nav_options = ["Home", "Gallery", "My Pass", "Create Content", "Marketplace", "Settings"]
        selected = st.radio("Go to", nav_options, index=nav_options.index(st.session_state.selected_page), 
                           label_visibility="collapsed", key="nav_radio")
        
        if selected != st.session_state.selected_page:
            st.session_state.selected_page = selected
            st.rerun()
    
    # Main content
    st.markdown('<h1 class="main-header">NSFW-Powered Universal Creator Pass</h1>', 
               unsafe_allow_html=True)
    
    # ===== HOME PAGE ===== (same as before)
    if st.session_state.selected_page == "Home":
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("## 🌐 Cross-Platform Membership")
            st.markdown("""
            Your Universal Creator Pass provides:
            
            - 🔓 **Access** to exclusive NSFW content
            - 💎 **Multi-chain** support (Ethereum, Polygon)
            - 🎨 **Creator tools** for content management
            - 💰 **Monetization** options
            - 🔒 **Privacy-preserving** features
            """)
            
            # Stats
            st.markdown("### 📊 Platform Stats")
            col1a, col2a, col3a = st.columns(3)
            with col1a:
                st.metric("Active Members", "1,234", "+12%")
            with col2a:
                st.metric("Total Content", "5,678", "+8%")
            with col3a:
                st.metric("Volume", "45.6 ETH", "+23%")
        
        with col2:
            st.markdown("## 🚀 Quick Actions")
            if st.button("🎫 Buy Pass", use_container_width=True):
                st.session_state.selected_page = "Marketplace"
                st.rerun()
            
            if st.button("🖼️ Upload Content", use_container_width=True):
                st.session_state.selected_page = "Create Content"
                st.rerun()
            
            if st.button("📊 View Analytics", use_container_width=True):
                st.info("Analytics dashboard coming soon!")
    
    # ===== GALLERY PAGE ===== (UPDATED FOR LOCAL IMAGES)
    elif st.session_state.selected_page == "Gallery":
        st.markdown("## 🖼️ NSFW Content Gallery")
        
        # NSFW warning
        st.markdown('<div class="nsfw-warning">🔞 18+ CONTENT - MEMBERS ONLY</div>', 
                   unsafe_allow_html=True)
        
        # Check for local images
        local_images = get_local_images()
        has_local_images = len(local_images) > 0
        
        # Show image source info
        col_info1, col_info2 = st.columns([1, 1])
        with col_info1:
            st.info(f"📁 Local images found: {len(local_images)}")
        with col_info2:
            if has_local_images:
                st.success("✅ Using local image files")
            else:
                st.warning("⚠️ No local images found. Using placeholders.")
        
        if not st.session_state.is_member:
            st.warning("You need a Creator Pass to view this content")
            if st.button("Get Creator Pass"):
                st.session_state.selected_page = "Marketplace"
                st.rerun()
        else:
            # Get gallery items (local if available, otherwise placeholders)
            if has_local_images:
                gallery_items = local_images
            else:
                gallery_items = [
                    {"img": "https://via.placeholder.com/600x400/FF6B6B/FFFFFF?text=Exclusive+1", 
                     "title": "Exclusive Artwork #1", "price": "0.1 ETH", "is_local": False},
                    {"img": "https://via.placeholder.com/600x400/4ECDC4/FFFFFF?text=NSFW+Photo", 
                     "title": "Premium Photo Set", "price": "0.05 ETH", "is_local": False},
                    {"img": "https://via.placeholder.com/600x400/FFD166/FFFFFF?text=Creator+Content", 
                     "title": "Creator Collection", "price": "0.2 ETH", "is_local": False},
                    {"img": "https://via.placeholder.com/600x400/06D6A0/FFFFFF?text=VIP+Access", 
                     "title": "VIP Exclusive", "price": "1 ETH", "is_local": False},
                    {"img": "https://via.placeholder.com/600x400/118AB2/FFFFFF?text=Animation", 
                     "title": "Animated Content", "price": "0.15 ETH", "is_local": False},
                    {"img": "https://via.placeholder.com/600x400/EF476F/FFFFFF?text=Special", 
                     "title": "Special Edition", "price": "0.3 ETH", "is_local": False},
                ]
            
            # Gallery HTML
            gallery_html = """
            <div class="gallery">
            """
            
            for item in gallery_items:
                # Add local badge for local images
                local_badge = '<span class="local-badge">LOCAL</span>' if item.get("is_local", False) else ''
                
                gallery_html += f"""
                <div class="gallery-item" style="position: relative;">
                    {local_badge}
                    <a target="_blank" href="{item['img']}">
                        <img src="{item['img']}" alt="{item['title']}">
                    </a>
                    <div class="desc">
                        {item['title']}<br>
                        <span class="price">{item['price']}</span>
                    </div>
                </div>
                """
            
            gallery_html += "</div>"
            
            st.markdown(gallery_html, unsafe_allow_html=True)
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                st.selectbox("Category", ["All", "Art", "Photos", "Videos", "Animations"], key="category_filter")
            with col2:
                st.selectbox("Price Range", ["All", "Free", "< 0.1 ETH", "0.1-0.5 ETH", "> 0.5 ETH"], key="price_filter")
            with col3:
                st.selectbox("Sort By", ["Newest", "Popular", "Price: Low to High", "Price: High to Low"], key="sort_filter")
    
    # ===== CREATE CONTENT PAGE ===== (UPDATED TO SAVE FILES)
    elif st.session_state.selected_page == "Create Content":
        st.markdown("## 🎨 Create NSFW Content")
        
        if not st.session_state.is_member:
            st.warning("You need a Creator Pass to upload content")
            st.stop()
        
        with st.form("upload_form"):
            title = st.text_input("Title", value="My Artwork")
            description = st.text_area("Description", value="A beautiful NSFW artwork")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", ["Art", "Photo", "Video", "Audio", "Other"])
                is_exclusive = st.checkbox("Exclusive Content")
            with col2:
                price = st.number_input("Price (ETH)", min_value=0.0, step=0.01, value=0.1)
                nsfw_level = st.select_slider("NSFW Level", ["Mild", "Moderate", "Explicit"])
            
            uploaded_file = st.file_uploader("Upload Content", type=['jpg', 'png', 'mp4', 'gif'])
            
            if st.form_submit_button("Upload Content", type="primary"):
                if uploaded_file:
                    try:
                        # Save the file locally
                        file_path = save_uploaded_file(uploaded_file)
                        file_name = os.path.basename(file_path)
                        
                        # Display preview
                        if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            img = Image.open(uploaded_file)
                            st.image(img, caption="Preview", use_column_width=True)
                        
                        # Generate content hash
                        file_bytes = uploaded_file.getvalue()
                        content_hash = hashlib.sha256(file_bytes).hexdigest()[:20]
                        
                        # Store in database
                        with SessionLocal() as db:
                            new_content = NSFWContent(
                                creator_id=1,  # Replace with actual user ID
                                content_hash=content_hash,
                                title=title,
                                description=description,
                                category=category,
                                is_exclusive=is_exclusive,
                                price_eth=str(price),
                                price_matic="0",  # Placeholder
                                nsfw_level=nsfw_level,
                                file_path=file_path  # Save the file path
                            )
                            db.add(new_content)
                            db.commit()
                            
                            st.success("✅ Content uploaded and saved successfully!")
                            st.info(f"📁 File saved to: {file_path}")
                            st.info(f"🔗 Content hash: {content_hash}...")
                            st.info(f"📛 NSFW level: {nsfw_level}")
                            
                            # Option to add to gallery immediately
                            if st.button("Add to Gallery"):
                                # Copy to images directory for gallery display
                                import shutil
                                gallery_path = os.path.join(Config.IMAGES_DIR, file_name)
                                shutil.copy2(file_path, gallery_path)
                                st.success(f"✅ Added to gallery: {gallery_path}")
                                st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing file: {e}")
                else:
                    st.warning("⚠️ Please upload a file")
    
    # ===== MY PASS PAGE ===== (same as before)
    elif st.session_state.selected_page == "My Pass":
        st.markdown("## 🎫 My Creator Pass")
        
        if not st.session_state.wallet_address:
            st.warning("Connect your wallet first")
        else:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image("https://via.placeholder.com/300x300/4ECDC4/FFFFFF?text=Creator+Pass+NFT", 
                        width=300)
                
                if st.session_state.is_member:
                    st.success("✅ Active Membership")
                    st.metric("Tier", "Premium", "VIP")
                    st.metric("Expires", "2024-12-31", "90 days")
                else:
                    st.error("❌ No Active Pass")
                    if st.button("Purchase Pass", type="primary"):
                        st.session_state.selected_page = "Marketplace"
                        st.rerun()
            
            with col2:
                st.markdown("### Pass Details")
                
                # Content access
                st.markdown("#### 🔓 Content Access")
                access_cols = st.columns(3)
                with access_cols[0]:
                    st.metric("Total Access", "45")
                with access_cols[1]:
                    st.metric("NSFW Content", "23")
                with access_cols[2]:
                    st.metric("Exclusive", "12")
                
                # Recent activity
                st.markdown("#### 📈 Recent Activity")
                activity_data = {
                    "Date": ["2024-01-15", "2024-01-10", "2024-01-05"],
                    "Action": ["Viewed Content", "Uploaded Art", "Renewed Pass"],
                    "Details": ["Exclusive Art #1", "My Collection #3", "VIP Tier"]
                }
                st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
    
    # ===== MARKETPLACE PAGE ===== (same as before)
    elif st.session_state.selected_page == "Marketplace":
        st.markdown("## 🛒 Marketplace")
        
        # Available passes
        st.markdown("### Available Passes")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🥉 Basic Pass")
            st.markdown("""
            - Access to basic content
            - Limited uploads
            - Community features
            """)
            st.metric("Price", "0.05 ETH")
            if st.button("Buy Basic", key="basic"):
                st.info("Processing purchase...")
        
        with col2:
            st.markdown("#### 🥈 Premium Pass")
            st.markdown("""
            - All basic features
            - NSFW content access
            - Increased upload limits
            - Analytics dashboard
            """)
            st.metric("Price", "0.1 ETH")
            if st.button("Buy Premium", key="premium", type="primary"):
                st.info("Processing purchase...")
        
        with col3:
            st.markdown("#### 🥇 VIP Pass")
            st.markdown("""
            - All premium features
            - Exclusive content
            - Priority support
            - Revenue sharing
            - Custom features
            """)
            st.metric("Price", "0.5 ETH")
            if st.button("Buy VIP", key="vip"):
                st.info("Processing purchase...")
    
    # ===== SETTINGS PAGE ===== (same as before)
    elif st.session_state.selected_page == "Settings":
        st.markdown("## ⚙️ Settings")
        
        tab1, tab2 = st.tabs(["Account", "Privacy"])
        
        with tab1:
            username = st.text_input("Username", value="crypto_creator")
            email = st.text_input("Email", value="creator@example.com")
            bio = st.text_area("Bio", value="Digital artist exploring NSFW content")
            st.file_uploader("Profile Picture", type=['jpg', 'png'])
            enable_nsfw = st.checkbox("Enable NSFW Content", value=True)
            
            if st.button("Save Changes", type="primary"):
                with SessionLocal() as db:
                    user = db.query(User).filter(User.wallet_address == st.session_state.wallet_address).first()
                    if user:
                        user.username = username
                        user.email = email
                        user.bio = bio
                        user.nsfw_enabled = enable_nsfw
                        db.commit()
                        st.success("Settings saved!")
        
        with tab2:
            st.checkbox("Show wallet publicly", value=True)
            st.checkbox("Allow content downloads", value=False)
            st.checkbox("Receive notifications", value=True)
            st.selectbox("Default Network", ["Ethereum", "Polygon", "Arbitrum"])
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🔐 NSFW Universal Creator Pass • Powered by Web3.py • Multi-chain Support</p>
        <p>⚠️ 18+ Only • All transactions are irreversible • Secure your private keys</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# SECTION 6: RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    main()
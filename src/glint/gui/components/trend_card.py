import customtkinter as ctk
import webbrowser

class TrendCard:
    @staticmethod
    def create(parent, trend, topic_name, scroll_handler):
        """Factory function to create a single trend card widget."""
        # CARD CONTAINER
        card = ctk.CTkFrame(parent, fg_color=("gray90", "gray13"))
        
        # 1. TITLE
        title_text = f"[{trend.category.upper()}] {trend.title}"
        title = ctk.CTkLabel(card, text=title_text, anchor="w", font=("Roboto", 12, "bold"))
        title.pack(fill="x", padx=10, pady=(10, 2))
        
        # 2. DESCRIPTION
        desc_text = trend.description if trend.description else "No description available"
        if len(desc_text) > 100:
            desc_text = desc_text[:100] + '...'
        desc = ctk.CTkLabel(card, text=desc_text, anchor="w", justify="left", wraplength=300, 
                           font=("Roboto", 11), text_color=("gray30", "gray70"))
        desc.pack(fill="x", padx=10, pady=(0, 5))
        
        # 3. META-INFORMATIONS and Badge information
        meta_frame = ctk.CTkFrame(card, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Date
        date_str = trend.published_at.strftime("%Y-%m-%d %H:%M")
        meta = ctk.CTkLabel(meta_frame, text=f"{trend.source} . {date_str}", 
                           font=("Roboto", 10), text_color="gray")
        meta.pack(side="left")
        
        # Right: Container for badge and link
        right_box = ctk.CTkFrame(meta_frame, fg_color="transparent")
        right_box.pack(side="right")
        
        # Badge (Only if topic_name exists)
        if topic_name:
            badge = ctk.CTkLabel(right_box, text=topic_name, fg_color="#3B8ED0", 
                                text_color="white", font=("Roboto", 9, "bold"), corner_radius=6)
            badge.pack(side="top", anchor="e", pady=(0, 2))
        
        # Link
        link = ctk.CTkLabel(right_box, text="See more", font=("Roboto", 10, "bold"), 
                           text_color=("blue", "#4da6ff"), cursor="hand2")
        link.pack(side="top", anchor="e")
        link.bind("<Button-1>", lambda e, u=trend.url: webbrowser.open(u))
        
        # === BIND GLOBAL SCROLL TO ALL WIDGETS ===
        scroll_handler.bind_recursive(card)
        
        return card

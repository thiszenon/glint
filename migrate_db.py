"""
Migration script to add content_fingerprint field.
Run this ONCE after updating the Trend model.
"""
from sqlmodel import Session, select, text
from glint.core.database import get_engine
from glint.core.models import Trend
from glint.utils.fingerprint import generate_fingerprint
def migrate():
    """Add content fingerprints to all trends."""
    engine = get_engine()
    
    # Step 1: Add column to database
    print("Step 1: Adding content_fingerprint column...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trend ADD COLUMN content_fingerprint VARCHAR"))
            conn.commit()
            print("✓ Added content_fingerprint column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("✓ content_fingerprint column already exists")
            else:
                print(f"⚠ Error adding column: {e}")
                return
    
    # Step 2: Generate fingerprints for existing trends
    print("\nStep 2: Generating fingerprints for existing trends...")
    with Session(engine) as session:
        # Get trends without fingerprints
        statement = select(Trend).where(
            (Trend.content_fingerprint == None) | (Trend.content_fingerprint == "")
        )
        trends = session.exec(statement).all()
        
        print(f"Found {len(trends)} trends to fingerprint...")
        
        for i, trend in enumerate(trends, 1):
            # Generate fingerprint
            trend.content_fingerprint = generate_fingerprint(
                trend.title,
                trend.description
            )
            
            # Progress indicator
            if i % 100 == 0:
                print(f"Processed {i}/{len(trends)} trends...")
        
        # Save all changes
        session.commit()
        print(f"\n✓ Migration complete! Fingerprinted {len(trends)} trends.")
        
        # Step 3: Find duplicates (analysis)
        print("\nStep 3: Analyzing duplicates...")
        statement = select(Trend.content_fingerprint).where(
            Trend.content_fingerprint != None
        )
        all_fingerprints = session.exec(statement).all()
        
        # Count duplicates
        from collections import Counter
        fingerprint_counts = Counter(all_fingerprints)
        duplicates = {fp: count for fp, count in fingerprint_counts.items() if count > 1}
        
        if duplicates:
            print(f"\n📊 Found {len(duplicates)} duplicate fingerprints:")
            # Show top 5 most duplicated
            top_dupes = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]
            for fp, count in top_dupes:
                print(f"  - Fingerprint {fp}: {count} instances")
                # Show titles
                dupe_trends = session.exec(
                    select(Trend).where(Trend.content_fingerprint == fp).limit(3)
                ).all()
                for trend in dupe_trends:
                    print(f"    → {trend.title[:60]}... ({trend.source})")
            
            total_dupes = sum(count - 1 for count in duplicates.values())
            print(f"\n💡 Potential savings: {total_dupes} duplicate trends")
        else:
            print("✓ No cross-platform duplicates found")
if __name__ == "__main__":
    migrate()
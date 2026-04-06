from scraper import KiryuHandler, SuminoeHandler

def test_rest():
    hd = "20260405"
    rno = 1
    
    # KIRYU
    print(f"--- Kiryu Recon (HD:{hd} RNO:{rno}) ---")
    h_kiryu = KiryuHandler()
    d_kiryu = h_kiryu.fetch_direct_data(rno, hd)
    print(f" Kiryu: {len(d_kiryu.get('exhibitions', []))} boats found.")
    
    # SUMINOE
    print(f"--- Suminoe Recon (HD:{hd} RNO:{rno}) ---")
    h_suminoe = SuminoeHandler()
    d_suminoe = h_suminoe.fetch_direct_data(rno, hd)
    print(f" Suminoe: {len(d_suminoe.get('exhibitions', []))} boats found.")

if __name__ == "__main__":
    test_rest()

import type { Metadata } from "next";
import Link from "next/link";
import SiteNav from "./site-nav";
import "./globals.css";
export const metadata:Metadata={title:"Black Flag Racing | AMS2 Championship",description:"Black Flag Racing Fall 2026 Automobilista 2 Championship standings, schedule and race results"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><header className="topbar"><Link className="brand" href="/"><span className="brand-fallback">BFR</span><img src="/bfr-logo.webp" alt="" className="header-logo"/></Link><SiteNav/></header><main className="shell">{children}</main><footer>BLACK FLAG RACING · FALL 2026 · AUTOMOBILISTA 2</footer></body></html>}

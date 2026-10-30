"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
const links=[["/","Overview"],["/standings","Standings"],["/calendar","Calendar"],["/results","Results"],["/points","Points Breakdown"],["/drivers","Drivers"]] as const;
export default function SiteNav(){
 const pathname=usePathname();
 const [open,setOpen]=useState(false);
 return <div className="nav-shell">
   <button type="button" className="menu-toggle" aria-label={open?"Close navigation menu":"Open navigation menu"} aria-expanded={open} aria-controls="primary-navigation" onClick={()=>setOpen(!open)}>
    <span aria-hidden="true">{open?"✕":"☰"}</span><span>Menu</span>
   </button>
   <nav id="primary-navigation" aria-label="Main navigation" className={open?"site-nav is-open":"site-nav"}>
    {links.map(([href,label])=><Link key={href} href={href} aria-current={pathname===href?"page":undefined} onClick={()=>setOpen(false)}>{label}</Link>)}
   </nav>
 </div>;
}

import type {Metadata} from "next";
import {WorkspaceProvider} from "@/components/workspace";
import {WalletProvider} from "@/components/wallet-provider";
import CursorGlow from "@/components/cursor-glow";
import "./globals.css";
export const metadata:Metadata={title:"Solana Quant Research Lab",description:"Reproducible on-chain factor research, event-driven backtesting and chronological validation."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><CursorGlow/><WalletProvider><WorkspaceProvider>{children}</WorkspaceProvider></WalletProvider></body></html>;}

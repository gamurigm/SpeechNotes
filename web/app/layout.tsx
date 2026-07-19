import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { BackgroundSystem } from "./dashboard/components/BackgroundSystem";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const stripExtensionHydrationAttrs = `
(function () {
  var attrs = ["fdprocessedid"];

  function removeAttrs(root) {
    if (!root) return;
    attrs.forEach(function (attr) {
      if (root.nodeType === 1 && root.hasAttribute && root.hasAttribute(attr)) {
        root.removeAttribute(attr);
      }
      if (root.querySelectorAll) {
        root.querySelectorAll("[" + attr + "]").forEach(function (el) {
          el.removeAttribute(attr);
        });
      }
    });
  }

  removeAttrs(document.documentElement);

  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.type === "attributes" && attrs.indexOf(mutation.attributeName) !== -1) {
        mutation.target.removeAttribute(mutation.attributeName);
      }
      mutation.addedNodes.forEach(removeAttrs);
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: attrs,
    childList: true,
    subtree: true
  });

  window.addEventListener("load", function () {
    window.setTimeout(function () {
      removeAttrs(document.documentElement);
      observer.disconnect();
    }, 5000);
  });
})();
`;
export const viewport: Viewport = {
  themeColor: "#000000",
};

export const metadata: Metadata = {
  title: "SpeechNotes",
  description: "Sistema de transcripción y toma de notas inteligente",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "SpeechNotes",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Script
          id="strip-extension-hydration-attrs"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{ __html: stripExtensionHydrationAttrs }}
        />
        <Providers>
          <BackgroundSystem />
          {children}
        </Providers>
      </body>
    </html>
  );
}

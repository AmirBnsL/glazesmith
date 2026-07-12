"use client";

import { motion, useReducedMotion } from "framer-motion";

export function CloudBackground() {
  const prefersReducedMotion = useReducedMotion();

  const clouds = [
    { top: "10%", left: "5%", width: 600, height: 400, delay: 0, duration: 24, x: [0, 80, -60, 0], y: [0, -70, 50, 0] },
    { top: "40%", right: "10%", width: 700, height: 500, delay: -5, duration: 30, x: [0, -90, 70, 0], y: [0, 60, -80, 0] },
    { bottom: "10%", left: "30%", width: 800, height: 600, delay: -10, duration: 18, x: [0, 60, -100, 0], y: [0, -50, 90, 0] },
  ];

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
      {clouds.map((cloud, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full bg-[var(--cloud)] blur-3xl opacity-[0.85]"
          style={{
            top: cloud.top,
            left: cloud.left,
            right: cloud.right,
            bottom: cloud.bottom,
            width: cloud.width,
            height: cloud.height,
          }}
          animate={prefersReducedMotion ? {} : {
            x: cloud.x,
            y: cloud.y,
            scale: [1, 1.08, 0.96, 1],
            borderRadius: [
              "60% 40% 30% 70%/60% 30% 70% 40%",
              "30% 60% 70% 40%/50% 60% 30% 60%",
              "50% 50% 40% 60%/40% 70% 50% 50%",
              "60% 40% 30% 70%/60% 30% 70% 40%"
            ],
          }}
          transition={{
            duration: cloud.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: cloud.delay,
          }}
        />
      ))}
    </div>
  );
}

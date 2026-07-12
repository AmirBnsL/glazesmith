"use client";

import { Canvas } from "@react-three/fiber";
import { useGLTF, Environment, ContactShadows, Clone } from "@react-three/drei";
import { Suspense, useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { useReducedMotion } from "framer-motion";
import * as THREE from "three";

function Vase() {
  const ref = useRef<THREE.Group>(null);
  const { scene } = useGLTF("/models/vase.glb");
  const prefersReducedMotion = useReducedMotion();

  useFrame((_, delta) => {
    if (ref.current && !prefersReducedMotion) {
      ref.current.rotation.y += delta * 0.35; // slow, constant
    }
  });

  const minY = useMemo(() => {
    const box = new THREE.Box3().setFromObject(scene);
    return box.min.y;
  }, [scene]);

  return (
    <group position={[0, -1.3, 0]} scale={0.8}>
      <group ref={ref}>
        <Clone object={scene} />
      </group>
      <ContactShadows position={[0, minY, 0]} scale={3.5} opacity={0.5} blur={3.5} far={3} frames={1} />
    </group>
  );
}

export default function VaseCanvas() {
  return (
    <Canvas 
      camera={{ position: [0, 0.5, 4], fov: 40 }} 
      className="!absolute inset-0" 
      gl={{ powerPreference: "high-performance", antialias: true, preserveDrawingBuffer: false, alpha: true }} 
      dpr={[1, 1.5]}
      onCreated={({ gl }) => {
        gl.domElement.addEventListener('webglcontextlost', (e) => {
          e.preventDefault(); console.error('WebGL context lost', e);
        });
        gl.domElement.addEventListener('webglcontextrestored', () => {
          console.log('WebGL context restored');
        });
      }}
    >
      <ambientLight intensity={1} />
      <directionalLight position={[0, 0, 10]} intensity={4} color="#e63e76ff" />
      {/* <Environment preset="studio" /> */}
      <Suspense fallback={null}>
        <Vase />
      </Suspense>
    </Canvas>
  );
}

useGLTF.preload("/models/vase.glb");

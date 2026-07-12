"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls, Environment, ContactShadows } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

// --- Tweakable variables for the 3D preview ---
const CAMERA_POSITION: [number, number, number] = [0, 0, 4];
const CAMERA_FOV = 45;
const ORBIT_TARGET: [number, number, number] = [0, 0, 0];
const VASE_POSITION: [number, number, number] = [0, -1, 0];
const VASE_SCALE = 2;
// ----------------------------------------------

interface GlazeVasePreviewProps {
  source: string | null;
  colorFallback: string | null;
}

function VaseModel({ source, colorFallback }: GlazeVasePreviewProps) {
  const { scene } = useGLTF("/models/simple_glass_vase.glb");
  const materialRef = useRef<THREE.MeshStandardMaterial | null>(null);
  const currentTextureRef = useRef<THREE.Texture | null>(null);

  // Deep clone scene and materials to ensure Hero vase isn't affected
  const clonedScene = useMemo(() => {
    const clone = scene.clone(true);
    clone.traverse((node) => {
      if (node instanceof THREE.Mesh) {
        node.material = node.material.clone();
        // Assume the vase has one primary material we want to edit.
        // We capture the first material we see to apply textures to.
        if (!materialRef.current) {
          materialRef.current = node.material as THREE.MeshStandardMaterial;
        }
      }
    });
    return clone;
  }, [scene]);

  // Handle cleanup of textures on unmount
  useEffect(() => {
    return () => {
      if (currentTextureRef.current) {
        currentTextureRef.current.dispose();
      }
    };
  }, []);

  // Apply material
  useEffect(() => {
    if (!materialRef.current) return;
    const material = materialRef.current;

    // Clean up previous texture
    if (currentTextureRef.current) {
      currentTextureRef.current.dispose();
      currentTextureRef.current = null;
    }

    if (source) {
      // Load and apply texture
      const loader = new THREE.TextureLoader();
      loader.load(
        source,
        (texture) => {
          texture.colorSpace = THREE.SRGBColorSpace;
          texture.wrapS = THREE.RepeatWrapping;
          texture.wrapT = THREE.RepeatWrapping;
          texture.repeat.set(3, 3); // Reduce stretching
          
          currentTextureRef.current = texture;
          material.map = texture;
          material.color = new THREE.Color(0xffffff); // Reset base color
          material.needsUpdate = true;
        },
        undefined,
        (error) => {
          console.error("Error loading glaze texture", error);
        }
      );
    } else if (colorFallback) {
      // Apply flat color fallback
      material.map = null;
      material.color = new THREE.Color(colorFallback);
      material.needsUpdate = true;
    } else {
      // Default state if nothing is provided
      material.map = null;
      material.color = new THREE.Color(0xcccccc);
      material.needsUpdate = true;
    }
  }, [source, colorFallback]);

  // Calculate minY for perfect shadow alignment
  const minY = useMemo(() => {
    const box = new THREE.Box3().setFromObject(clonedScene);
    return box.min.y;
  }, [clonedScene]);

  return (
    <group position={VASE_POSITION} scale={VASE_SCALE}>
      <primitive object={clonedScene} />
      <ContactShadows position={[0, minY, 0]} scale={3} opacity={0.4} blur={2.5} far={3} frames={1} />
    </group>
  );
}

export default function GlazeVasePreview({ source, colorFallback }: GlazeVasePreviewProps) {
  return (
    <Canvas
      camera={{ position: CAMERA_POSITION, fov: CAMERA_FOV }}
      className="!absolute inset-0"
      gl={{ powerPreference: "high-performance", antialias: true, alpha: true }}
      dpr={[1, 1.5]}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={1.5} />
      <directionalLight position={[-5, 5, 5]} intensity={0.5} />
      <Environment preset="studio" />
      
      <Suspense fallback={null}>
        <VaseModel source={source} colorFallback={colorFallback} />
      </Suspense>
      
      <OrbitControls target={ORBIT_TARGET} autoRotate autoRotateSpeed={2} enablePan={false} enableZoom={true} />
    </Canvas>
  );
}

useGLTF.preload("/models/simple_glass_vase.glb");

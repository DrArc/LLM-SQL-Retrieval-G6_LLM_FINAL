import { IfcViewerAPI } from "web-ifc-viewer"

async function main() {
  const container = document.getElementById("viewer")
  const viewer = new IfcViewerAPI({ container })

  await viewer.context.ifcLoader.ifcManager.useWebWorkers(
    true,
    "./IFCWorker.js"
  )

  document.getElementById("file-input").addEventListener("change", async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const url = URL.createObjectURL(file)
    await viewer.IFC.loadIfcUrl(url)
  })
}

main()

// Ensure the viewer is initialized after the DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
  main().catch((error) => {
    console.error("Error initializing the viewer:", error)
  })
})

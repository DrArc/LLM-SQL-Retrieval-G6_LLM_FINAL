import { Viewer, DefaultViewerParams, SpeckleLoader, UrlHelper,
         CameraController, MeasurementsExtension } from "@speckle/viewer";
window.startSpeckleViewer = startSpeckleViewer;



export async function startSpeckleViewer(url, token = "") {
  const container = document.getElementById("renderer");
  const params = DefaultViewerParams;
  params.verbose = true;

  const viewer = new Viewer(container, params);
  await viewer.init();
  viewer.createExtension(CameraController);
  viewer.createExtension(MeasurementsExtension);

  const urls = await UrlHelper.getResourceUrls(url, token);
  for (const u of urls) {
    const loader = new SpeckleLoader(viewer.getWorldTree(), u, token);
    await viewer.loadObject(loader, true);
  }
}




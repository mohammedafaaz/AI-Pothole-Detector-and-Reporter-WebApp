import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera } from 'lucide-react';
import { useAppStore } from '../store';
import { Detection } from '../types';
import { getCurrentLocation, getAddressFromCoordinates } from '../utils/location';
import CameraCapture from './CameraCapture';
import usePotholeDetection from '../hooks/usePotholeDetection';
import DetectionProgressBar from './DetectionProgressBar';

const ReportForm: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, addReport } = useAppStore();
  const { detectFromBase64, loading: apiLoading } = usePotholeDetection();

  const [showCamera, setShowCamera] = useState(false);
  const [photo, setPhoto] = useState<string | null>(null);
  const [description, setDescription] = useState('');
  const [detections, setDetections] = useState<Detection[]>([]);
  const [severity, setSeverity] = useState<'high' | 'medium' | 'low'>('low');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [annotatedImageUrl, setAnnotatedImageUrl] = useState<string | null>(null);
  const [potholeDetected, setPotholeDetected] = useState<boolean>(false);

  // Progress bar states
  const [showProgress, setShowProgress] = useState<boolean>(false);
  const [progressStep, setProgressStep] = useState<'capturing' | 'uploading' | 'processing' | 'analyzing' | 'complete' | 'error'>('capturing');
  const [progressValue, setProgressValue] = useState<number>(0);
  const [progressMessage, setProgressMessage] = useState<string>('');

  const handleOpenCamera = () => {
    setShowCamera(true);
  };

  const handleCameraCapture = async (
    capturedPhoto: string,
    capturedDetections: Detection[],
    detectedSeverity: 'high' | 'medium' | 'low'
  ) => {
    setPhoto(capturedPhoto);
    setDetections(capturedDetections);
    setSeverity(detectedSeverity);
    setShowCamera(false);
    setPotholeDetected(false);

    // Start progress bar after camera closes
    setTimeout(() => {
      setShowProgress(true);
      setProgressStep('capturing');
      setProgressValue(10);
      setProgressMessage('Image captured successfully!');
    }, 100);

    // Process the captured image through Flask API
    try {
      // Step 1: Uploading
      setProgressStep('uploading');
      setProgressValue(25);
      setProgressMessage('Uploading image to our AI...');
      await new Promise(resolve => setTimeout(resolve, 500)); // Small delay for UX
      // Step 2: Processing
      setProgressStep('processing');
      setProgressValue(50);
      setProgressMessage('Our AI is Analyzing...');

      let locationData: { latitude: number; longitude: number } | undefined = undefined;
      try {
        const position = await getCurrentLocation();
        locationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        console.log('Location captured for email:', locationData);
      } catch (error) {
        console.warn('Could not get location for detection:', error);
      }

      // Step 3: AI Analysis
      setProgressStep('analyzing');
      setProgressValue(75);
      setProgressMessage('Our AI model is working at its best. Hold on! ');

      const result = await detectFromBase64(capturedPhoto, {
        includeImage: true,
        email: 'mohammedafaaz433@gmail.com', // Your email for reports
        sendEmail: true, // Always try to send email, Flask will decide based on detections
        location: locationData,
        userInfo: {
          name: currentUser?.name || 'Unknown User',
          email: currentUser?.email || 'N/A'
        }
      });

      // Update with API results
      setDetections(result.detections);
      setSeverity(result.severity);
      setAnnotatedImageUrl(result.annotatedImageUrl || null);

      // Check if potholes were actually detected
      const hasValidPotholes = result.detections.length > 0 &&
        result.detections.some(detection =>
          detection.class.toLowerCase().includes('pothole') &&
          detection.confidence > 0.3 // Minimum confidence threshold
        );

      setPotholeDetected(hasValidPotholes);

      // Step 4: Complete
      setProgressStep('complete');
      setProgressValue(100);

      if (hasValidPotholes) {
        setProgressMessage(`✅ Detection complete! Found ${result.detections.length} pothole(s).`);
        setError(null);

        // Flask API will automatically send to both admin and user emails
      } else {
        setProgressMessage('❌ No potholes detected in this image.');
        setError('No potholes detected. Only Pothole(s) will be reported.');
      }

      console.log('Flask API detection completed:', result);

      // Hide progress bar after 2 seconds
      setTimeout(() => {
        setShowProgress(false);
      }, 2000);

    } catch (error) {
      console.error('Flask API detection failed:', error);

      // Show error in progress bar
      setProgressStep('error');
      setProgressValue(100);
      setProgressMessage('Detection failed. Using camera detection as normal.');

      // Fallback: allow submission but with warning
      setPotholeDetected(capturedDetections.length > 0);
      setError('API detection failed, using camera detection as normal');

      // Hide progress bar after 3 seconds
      setTimeout(() => {
        setShowProgress(false);
      }, 3000);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!photo) {
      setError('Please capture a photo of the pothole');
      return;
    }

    if (!potholeDetected) {
      setError('No potholes detected in the captured image. Please capture a clearer image of the pothole.');
      return;
    }


    
    if (!currentUser) {
      setError('You must be logged in to submit a report');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      // Get current location with high accuracy
      const position = await getCurrentLocation();
      const { latitude, longitude } = position.coords;
      
      // Get address from coordinates with better error handling
      let address;
      try {
        address = await getAddressFromCoordinates(latitude, longitude);
      } catch (error) {
        console.error('Error getting address:', error);
        address = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
      }
      
      // Create report with precise coordinates
      const reportData = {
        userId: currentUser.id,
        photo: annotatedImageUrl || photo, // Use annotated image if available
        description: description.trim() || undefined,
        severity,
        confidence: detections.reduce((sum, det) => sum + det.confidence, 0) /
                    (detections.length || 1),
        location: {
          lat: latitude,
          lng: longitude,
          address
        },
        originalPhoto: photo, // Keep original photo as backup
        annotatedImageUrl: annotatedImageUrl || undefined,
        upvotedBy: [],
        downvotedBy: []
      };
      
      // Add report to store
      addReport(reportData);
      
      // Navigate to home page
      navigate('/home');
    } catch (err) {
      console.error('Error submitting report:', err);
      
      // Check if the error is related to geolocation permission
      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError('Location access denied. Please enable location services to submit a report.');
            break;
          case err.POSITION_UNAVAILABLE:
            setError('Unable to determine your location. Please try again.');
            break;
          case err.TIMEOUT:
            setError('Location request timed out. Please try again.');
            break;
          default:
            setError('Failed to get location. Please try again.');
        }
      } else {
        setError('Failed to submit report. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 animate-pop-in">
      <h1 className="text-2xl font-bold mb-6">Report a Pothole</h1>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <label className="block text-gray-700 font-medium mb-2">
            Pothole Photo <span className="text-red-500">*</span>
          </label>
          
          {photo ? (
            <div className="relative">
              <img 
                src={photo} 
                alt="Captured pothole" 
                className="w-full h-48 object-cover rounded-lg"
              />
              <button
                type="button"
                onClick={handleOpenCamera}
                className="absolute bottom-2 right-2 bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-full"
                aria-label="Recapture photo"
              >
                <Camera size={20} />
              </button>
              

            </div>
          ) : (
            <button
              type="button"
              onClick={handleOpenCamera}
              className="w-full h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center bg-gray-50 hover:bg-gray-100"
            >
              <Camera size={36} className="text-gray-400 mb-2" />
              <span className="text-gray-500">Click to capture a photo</span>
            </button>
          )}
        </div>
        
        <div className="mb-6">
          <label htmlFor="description" className="block text-gray-700 font-medium mb-2">
            Description (Optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add any additional details about the pothole..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            rows={3}
          />
        </div>


        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        <div className="flex justify-between">
          <button
            type="button"
            onClick={() => navigate('/home')}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          
          <button
            type="submit"
            disabled={isSubmitting || !photo || apiLoading || !potholeDetected}
            className={`px-4 py-2 text-white rounded-lg transition-colors ${
              potholeDetected && !isSubmitting && !apiLoading
                ? 'bg-blue-500 hover:bg-blue-600'
                : 'bg-gray-400 cursor-not-allowed'
            }`}
            title={!potholeDetected ? 'No potholes detected in image' : ''}
          >
            {isSubmitting ? 'Submitting...' :
             apiLoading ? 'Processing...' :
             !potholeDetected ? 'No Potholes Detected' :
             'Submit Report'}
          </button>
        </div>
      </form>
      
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}

      {/* Detection Progress Bar */}
      <DetectionProgressBar
        isActive={showProgress}
        currentStep={progressStep}
        progress={progressValue}
        message={progressMessage}
        onComplete={() => setShowProgress(false)}
      />
    </div>
  );
};

export default ReportForm;
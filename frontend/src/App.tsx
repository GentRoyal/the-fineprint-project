import { useState, useRef } from 'react';
import { Upload, FileText, AlertTriangle, AlertCircle, Info, Trash2, CheckCircle, Shield, BarChart3, FileSearch, Menu, Headphones, Play, Pause, Volume2 } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Switch } from './components/ui/switch';
import { Label } from './components/ui/label';
import { motion, AnimatePresence } from 'motion/react';

interface Clause {
  id: string;
  text: string;
  riskLevel: 'high' | 'medium' | 'low';
  explanation: string;
}

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<Clause[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('upload');
  const [isDragging, setIsDragging] = useState(false);
  const [podcastMode, setPodcastMode] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      simulateUpload();
    }
  };

  const simulateUpload = () => {
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 100);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || file.type === 'text/plain')) {
      setSelectedFile(file);
      simulateUpload();
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile && !pastedText.trim()) return;

    setIsAnalyzing(true);
    
    try {
      const API_BASE_URL = 'http://localhost:8000'; // Change this to your API URL
      
      let response;
      
      if (podcastMode) {
        // Podcast Mode - Different endpoints
        if (selectedFile) {
          // Handle file upload for podcast
          const formData = new FormData();
          formData.append('file', selectedFile);
          
          response = await fetch(`${API_BASE_URL}/conversation_clauses_file`, {
            method: 'POST',
            body: formData,
          });
        } else {
          // Handle text paste for podcast
          response = await fetch(`${API_BASE_URL}/conversation_clauses`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: pastedText }),
          });
        }
        
        if (!response.ok) {
          throw new Error(`API Error: ${response.statusText}`);
        }
        
        // Handle audio response
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setResults([]); // Clear clause results when in podcast mode
      } else {
        // Regular Analysis Mode
        if (selectedFile) {
          // Handle file upload
          const formData = new FormData();
          formData.append('file', selectedFile);
          
          response = await fetch(`${API_BASE_URL}/get_clauses`, {
            method: 'POST',
            body: formData,
          });
        } else {
          // Handle text paste
          response = await fetch(`${API_BASE_URL}/get_clauses`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: pastedText }),
          });
        }
        
        if (!response.ok) {
          throw new Error(`API Error: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Transform API response to match our Clause interface
        const transformedResults: Clause[] = data.clauses?.map((clause: any, index: number) => ({
          id: clause.id || String(index + 1),
          text: clause.text || clause.clause_text || '',
          riskLevel: (clause.risk_level || clause.severity || 'medium').toLowerCase() as 'high' | 'medium' | 'low',
          explanation: clause.explanation || clause.reason || ''
        })) || [];
        
        setResults(transformedResults);
        setAudioUrl(null); // Clear audio when in regular mode
      }
    } catch (error) {
      console.error('Error analyzing document:', error);
      // Show error to user
      alert('Failed to analyze document. Please make sure your API is running on http://localhost:8000');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPastedText('');
    setResults([]);
    setUploadProgress(0);
    setAudioUrl(null);
    setIsPlaying(false);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation Header */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <span className="text-slate-900">Terms Transparency Tracker</span>
            </div>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-slate-700 hover:text-slate-900 transition-colors">
                Features
              </a>
              <a href="#how-it-works" className="text-slate-700 hover:text-slate-900 transition-colors">
                How It Works
              </a>
              <a href="#pricing" className="text-slate-700 hover:text-slate-900 transition-colors">
                Pricing
              </a>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center gap-3">
              <Button variant="ghost" className="text-slate-700 hover:text-slate-900">
                Log In
              </Button>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                Sign Up
              </Button>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <AnimatePresence>
          {results.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-16"
            >
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                {/* Left Content */}
                <div>
                  <Badge className="bg-teal-50 text-teal-700 border-teal-200 mb-6">
                    AI-Powered Analysis
                  </Badge>
                  <h1 className="text-slate-900 mb-6">
                    Understand Legal Documents in Seconds
                  </h1>
                  <p className="text-slate-600 text-lg mb-8 leading-relaxed">
                    Upload or paste any Terms & Conditions or Privacy Policy and get instant insights into potentially harmful clauses that could affect your rights.
                  </p>
                  
                  {/* Feature List */}
                  <div className="grid sm:grid-cols-3 gap-6 mb-8">
                    <div className="flex flex-col items-start gap-2">
                      <div className="w-12 h-12 bg-teal-50 rounded-lg flex items-center justify-center">
                        <FileSearch className="w-6 h-6 text-teal-600" />
                      </div>
                      <span className="text-sm text-slate-700">Smart Detection</span>
                    </div>
                    <div className="flex flex-col items-start gap-2">
                      <div className="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
                        <AlertTriangle className="w-6 h-6 text-orange-600" />
                      </div>
                      <span className="text-sm text-slate-700">Risk Assessment</span>
                    </div>
                    <div className="flex flex-col items-start gap-2">
                      <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                        <BarChart3 className="w-6 h-6 text-blue-600" />
                      </div>
                      <span className="text-sm text-slate-700">Detailed Reports</span>
                    </div>
                  </div>
                </div>

                {/* Right Image/Visual */}
                <div className="relative">
                  <div className="relative bg-white rounded-2xl shadow-2xl p-8 border border-slate-200">
                    <div className="absolute -top-4 -right-4 w-24 h-24 bg-teal-100 rounded-xl -z-10" />
                    <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-orange-50 rounded-xl -z-10" />
                    
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 pb-4 border-b border-slate-200">
                        <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
                          <FileText className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <div className="h-3 bg-slate-200 rounded w-3/4 mb-2" />
                          <div className="h-2 bg-slate-100 rounded w-1/2" />
                        </div>
                      </div>
                      
                      <div className="space-y-3">
                        <div className="flex gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="h-2 bg-red-200 rounded w-full" />
                            <div className="h-2 bg-red-200 rounded w-4/5" />
                          </div>
                        </div>
                        
                        <div className="flex gap-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                          <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="h-2 bg-orange-200 rounded w-full" />
                            <div className="h-2 bg-orange-200 rounded w-3/4" />
                          </div>
                        </div>
                        
                        <div className="flex gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />
                          <div className="flex-1 space-y-2">
                            <div className="h-2 bg-blue-200 rounded w-full" />
                            <div className="h-2 bg-blue-200 rounded w-2/3" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload/Paste Section */}
        <div className="space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="bg-white border-slate-200 shadow-lg">
              <div className="p-8">
                {/* Podcast Mode Toggle */}
                <div className="flex items-center justify-between p-4 mb-6 bg-gradient-to-r from-teal-50 to-blue-50 rounded-xl border border-teal-200">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
                      <Headphones className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="text-slate-900 font-medium">Podcast Mode</p>
                      <p className="text-sm text-slate-600">Generate an audio explanation instead of text analysis</p>
                    </div>
                  </div>
                  
                  {/* Custom Toggle */}
                  <button
                    onClick={() => setPodcastMode(!podcastMode)}
                    className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors flex-shrink-0 ${
                      podcastMode ? 'bg-teal-600' : 'bg-gray-300'
                    }`}
                    style={{
                      outline: 'none',
                    }}
                  >
                    <span
                      className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform ${
                        podcastMode ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 mb-8 bg-slate-100">
                    <TabsTrigger 
                      value="upload" 
                      className="flex items-center gap-2 data-[state=active]:bg-white"
                    >
                      <Upload className="w-4 h-4" />
                      Upload Document
                    </TabsTrigger>
                    <TabsTrigger 
                      value="paste" 
                      className="flex items-center gap-2 data-[state=active]:bg-white"
                    >
                      <FileText className="w-4 h-4" />
                      Paste Text
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="upload" className="space-y-6">
                    <div
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      className={`border-2 border-dashed rounded-xl p-16 text-center transition-all duration-200 cursor-pointer ${
                        isDragging 
                          ? 'border-teal-500 bg-teal-50' 
                          : 'border-slate-300 bg-slate-50 hover:border-teal-400 hover:bg-teal-50/50'
                      }`}
                    >
                      <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        accept=".pdf,.docx,.txt"
                        onChange={handleFileChange}
                      />
                      <label htmlFor="file-upload" className="cursor-pointer">
                        <div className="flex flex-col items-center gap-4">
                          <div className="w-16 h-16 bg-teal-600 rounded-xl flex items-center justify-center">
                            <Upload className="w-8 h-8 text-white" />
                          </div>
                          <div>
                            <p className="text-slate-900">
                              <span className="text-teal-600">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-sm text-slate-500 mt-2">PDF, DOCX, or TXT • Maximum file size 10MB</p>
                          </div>
                        </div>
                      </label>
                    </div>

                    <AnimatePresence>
                      {selectedFile && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="bg-slate-50 rounded-xl p-6 border border-slate-200"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 bg-teal-600 rounded-lg flex items-center justify-center">
                                <FileText className="w-6 h-6 text-white" />
                              </div>
                              <div>
                                <p className="text-slate-900">{selectedFile.name}</p>
                                <p className="text-sm text-slate-600">{(selectedFile.size / 1024).toFixed(2)} KB</p>
                              </div>
                            </div>
                            <CheckCircle className="w-6 h-6 text-green-600" />
                          </div>
                          {uploadProgress < 100 && (
                            <div className="mt-4">
                              <Progress value={uploadProgress} className="h-2" />
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </TabsContent>

                  <TabsContent value="paste">
                    <Textarea
                      placeholder="Paste your Terms & Conditions or Privacy Policy text here..."
                      value={pastedText}
                      onChange={(e) => setPastedText(e.target.value)}
                      className="min-h-[400px] resize-none border-slate-300 focus:border-teal-500 rounded-xl bg-slate-50"
                    />
                    <p className="text-sm text-slate-500 mt-3 flex items-center gap-2">
                      <Info className="w-4 h-4" />
                      Paste the full text of the legal document you want to analyze
                    </p>
                  </TabsContent>
                </Tabs>

                {/* Action Buttons */}
                <div className="flex gap-4 mt-8">
                  <Button
                    onClick={handleAnalyze}
                    disabled={(!selectedFile && !pastedText.trim()) || isAnalyzing}
                    className="flex-1 h-12 bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    {isAnalyzing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        {podcastMode ? 'Generating Podcast...' : 'Analyzing Document...'}
                      </>
                    ) : (
                      <>
                        {podcastMode ? <Headphones className="w-5 h-5 mr-2" /> : <FileSearch className="w-5 h-5 mr-2" />}
                        {podcastMode ? 'Generate Podcast' : 'Analyze Document'}
                      </>
                    )}
                  </Button>
                  {(selectedFile || pastedText || results.length > 0 || audioUrl) && (
                    <Button
                      onClick={handleClear}
                      variant="outline"
                      className="h-12 px-6 border-slate-300 hover:bg-slate-50"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clear
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Audio Player Section */}
          <AnimatePresence>
            {audioUrl && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Card className="bg-gradient-to-br from-teal-50 to-blue-50 border-teal-200 shadow-lg">
                  <div className="p-8">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-12 h-12 bg-teal-600 rounded-xl flex items-center justify-center">
                        <Headphones className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h2 className="text-slate-900">Podcast Generated</h2>
                        <p className="text-sm text-slate-600">Listen to the audio explanation of the document</p>
                      </div>
                    </div>

                    {/* Custom Audio Player */}
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <audio
                        ref={audioRef}
                        src={audioUrl}
                        onEnded={() => setIsPlaying(false)}
                        onPlay={() => setIsPlaying(true)}
                        onPause={() => setIsPlaying(false)}
                        className="hidden"
                      />
                      
                      <div className="flex items-center gap-4">
                        {/* Play/Pause Button */}
                        <Button
                          onClick={togglePlayPause}
                          size="icon"
                          className="w-14 h-14 rounded-full bg-teal-600 hover:bg-teal-700"
                        >
                          {isPlaying ? (
                            <Pause className="w-6 h-6 text-white" />
                          ) : (
                            <Play className="w-6 h-6 text-white ml-1" />
                          )}
                        </Button>

                        {/* Waveform/Progress Visualization */}
                        <div className="flex-1 flex items-center gap-2">
                          <Volume2 className="w-5 h-5 text-slate-400" />
                          <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-teal-600 to-blue-600 rounded-full transition-all duration-300" 
                                 style={{ width: isPlaying ? '50%' : '0%' }} />
                          </div>
                        </div>

                        {/* Download Button */}
                        <a
                          href={audioUrl}
                          download="podcast.wav"
                          className="text-sm text-teal-600 hover:text-teal-700 px-4 py-2 border border-teal-300 rounded-lg hover:bg-teal-50 transition-colors"
                        >
                          Download
                        </a>
                      </div>

                      {/* Native Audio Controls (Fallback) */}
                      
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results Section */}
          <AnimatePresence>
            {results.length > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-8"
              >
                {/* Results Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-slate-900 mb-2">Analysis Results</h2>
                    <p className="text-slate-600">We found {results.length} potential issues in this document</p>
                  </div>
                  <div className="flex gap-2">
                    <Badge className="bg-red-50 text-red-700 border-red-200">
                      {results.filter(r => r.riskLevel === 'high').length} High Risk
                    </Badge>
                    <Badge className="bg-orange-50 text-orange-700 border-orange-200">
                      {results.filter(r => r.riskLevel === 'medium').length} Medium
                    </Badge>
                    <Badge className="bg-blue-50 text-blue-700 border-blue-200">
                      {results.filter(r => r.riskLevel === 'low').length} Low
                    </Badge>
                  </div>
                </div>

                {/* Results Cards */}
                <div className="space-y-4">
                  {results.map((clause, index) => (
                    <motion.div
                      key={clause.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <Card className="bg-white border-slate-200 shadow-md hover:shadow-lg transition-shadow">
                        <div className="p-8">
                          <div className="flex items-start gap-6">
                            {/* Risk Icon */}
                            <div className={`flex-shrink-0 p-3 rounded-lg ${
                              clause.riskLevel === 'high' ? 'bg-red-100' :
                              clause.riskLevel === 'medium' ? 'bg-orange-100' :
                              'bg-blue-100'
                            }`}>
                              {clause.riskLevel === 'high' && <AlertTriangle className="w-6 h-6 text-red-600" />}
                              {clause.riskLevel === 'medium' && <AlertCircle className="w-6 h-6 text-orange-600" />}
                              {clause.riskLevel === 'low' && <Info className="w-6 h-6 text-blue-600" />}
                            </div>

                            {/* Content */}
                            <div className="flex-1 space-y-4">
                              <div>
                                <Badge className={`mb-4 ${
                                  clause.riskLevel === 'high' ? 'bg-red-50 text-red-700 border-red-200' :
                                  clause.riskLevel === 'medium' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                                  'bg-blue-50 text-blue-700 border-blue-200'
                                } border`}>
                                  {clause.riskLevel.toUpperCase()} RISK
                                </Badge>
                                <div className={`border-l-4 pl-6 py-2 ${
                                  clause.riskLevel === 'high' ? 'border-red-300' :
                                  clause.riskLevel === 'medium' ? 'border-orange-300' :
                                  'border-blue-300'
                                }`}>
                                  <p className="text-slate-700 italic">
                                    "{clause.text}"
                                  </p>
                                </div>
                              </div>
                              
                              <div className={`rounded-lg p-4 border ${
                                clause.riskLevel === 'high' ? 'bg-red-50 border-red-200' :
                                clause.riskLevel === 'medium' ? 'bg-orange-50 border-orange-200' :
                                'bg-blue-50 border-blue-200'
                              }`}>
                                <p className={`text-sm mb-1 ${
                                  clause.riskLevel === 'high' ? 'text-red-900' :
                                  clause.riskLevel === 'medium' ? 'text-orange-900' :
                                  'text-blue-900'
                                }`}>
                                  <strong>Why this matters:</strong>
                                </p>
                                <p className={
                                  clause.riskLevel === 'high' ? 'text-red-800' :
                                  clause.riskLevel === 'medium' ? 'text-orange-800' :
                                  'text-blue-800'
                                }>
                                  {clause.explanation}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </div>

                {/* Bottom CTA */}
                <Card className="bg-slate-50 border-slate-200">
                  <div className="p-8">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 bg-teal-600 rounded-xl flex items-center justify-center">
                          <FileText className="w-7 h-7 text-white" />
                        </div>
                        <div>
                          <h3 className="text-slate-900 mb-1">Need to analyze another document?</h3>
                          <p className="text-sm text-slate-600">Upload a new file or paste different text to continue</p>
                        </div>
                      </div>
                      <Button 
                        onClick={handleClear}
                        className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        Analyze Another
                      </Button>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-20 py-12 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-slate-700">Terms Transparency Tracker</span>
            </div>
            <p className="text-sm text-slate-600">
              © 2025 Terms Transparency Tracker. Helping you understand legal documents better.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

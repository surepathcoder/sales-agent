'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/auth';
import { useToast } from '@/components/ui/toast';
import { api } from '@/lib/api';
import { 
  Check, 
  Minus, 
  MessageCircle, 
  Star, 
  ArrowRight, 
  Search, 
  MessageSquare, 
  Languages, 
  Play, 
  Globe2,
  X,
  Loader2,
  Smartphone,
  ShieldCheck,
  Building,
  Mail,
  Phone,
  Lock,
  Compass,
  CreditCard
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// Typing simulation steps for WhatsApp Mockup
const WHATSAPP_CONVERSATION = [
  { sender: 'agent', text: 'Habari za asubuhi! Mimi ni mwakilishi wa kampuni ya bima. Tumeona biashara yako mtandaoni. Mnaweza kutusaidia kujua zaidi kuhusu bima za biashara? 🙏', time: '9:02' },
  { sender: 'lead', text: 'Habari! Ndio, tuna nia. Tuma maelezo zaidi.', time: '9:14' },
  { sender: 'agent', text: 'Asante! Bima zetu zinasaidia kulinda biashara yako dhidi ya majanga. Tunaweza kukutana wiki hii tuzungumze zaidi? Jumanne au Alhamisi?', time: '9:15' },
  { sender: 'lead', text: 'Jumanne nina nafasi. Lakini bei zenu zikoje?', time: '9:17' },
  { sender: 'agent', text: 'Tuna vifurushi kuanzia TZS 50,000 kwa mwezi kulingana na ukubwa wa biashara. Saa ngapi Jumanne itakuwa sawa kwako? Nitaandaa dondoo.', time: '9:18' },
  { sender: 'lead', text: 'Saa nne asubuhi. Tuma kalenda.', time: '9:25' },
  { sender: 'agent', text: 'Sawa kabisa. Nimekutumia mwaliko kwenye kalenda yako (Jumanne, Saa 4:00 Asubuhi). Asante na uwe na siku njema! ✨', time: '9:26' },
  { sender: 'lead', text: 'Asante.', time: '9:30' }
];

export default function LandingPage() {
  const router = useRouter();
  const { toast } = useToast();
  const token = useAuthStore((s) => s.accessToken);
  const setAuth = useAuthStore((s) => s.setAuth);

  // Core modal and interactive state
  const [activeModal, setActiveModal] = useState<'login' | 'register' | 'forgot_password' | 'demo' | 'checkout' | null>(null);
  const [checkoutPlan, setCheckoutPlan] = useState<'free' | 'growth' | 'agency' | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Form states
  const [loginForm, setLoginForm] = useState({ email: '', password: '', tenantSlug: '' });
  const [registerForm, setRegisterForm] = useState({ company_name: '', email: '', phone: '', password: '', industry_vertical: 'general', plan_type: 'free' });
  const [resetEmail, setResetEmail] = useState('');
  const [mpesaPhone, setMpesaPhone] = useState('');

  // Page dynamic states
  const [chatMessages, setChatMessages] = useState<typeof WHATSAPP_CONVERSATION>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // WhatsApp simulation loop
  useEffect(() => {
    let isActive = true;
    let timer: NodeJS.Timeout;
    let messageIndex = 0;

    const runChatLoop = () => {
      if (!isActive) return;
      setChatMessages([]);
      messageIndex = 0;
      
      const postNextMessage = () => {
        if (!isActive) return;
        if (messageIndex < WHATSAPP_CONVERSATION.length) {
          setIsTyping(true);
          // Simulate typing duration
          timer = setTimeout(() => {
            if (!isActive) return;
            setIsTyping(false);
            const msg = WHATSAPP_CONVERSATION[messageIndex];
            if (msg) {
              setChatMessages(prev => {
                // Prevent duplicates in Strict Mode
                if (prev.length > messageIndex) return prev;
                return [...prev, msg];
              });
            }
            messageIndex++;
            // Wait before next message
            timer = setTimeout(postNextMessage, 2500);
          }, 1500);
        } else {
          // Conversation finished, restart after delay
          timer = setTimeout(() => {
            if (isActive) runChatLoop();
          }, 6000);
        }
      };

      timer = setTimeout(postNextMessage, 1000);
    };

    runChatLoop();

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, []);

  // Listen for Escape key to dismiss modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeAllModals();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const closeAllModals = () => {
    setActiveModal(null);
    setCheckoutPlan(null);
    setLoginForm({ email: '', password: '', tenantSlug: '' });
    setRegisterForm({ company_name: '', email: '', phone: '', password: '', industry_vertical: 'general', plan_type: 'free' });
    setResetEmail('');
    setMpesaPhone('');
  };

  // Submit Handlers
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
        user: any;
        tenant: any;
      }>('/api/v1/auth/login', { 
        email: loginForm.email, 
        password: loginForm.password,
        tenant_slug: loginForm.tenantSlug || undefined 
      });
      setAuth(data);
      toast('Karibu tena! / Welcome back!', 'success');
      closeAllModals();
      router.push('/dashboard');
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Neno la siri au barua pepe sio sahihi', 'error');
    } finally {
      setModalLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
        user: any;
        tenant: any;
      }>('/api/v1/auth/register', {
        company_name: registerForm.company_name,
        email: registerForm.email,
        phone: registerForm.phone,
        password: registerForm.password,
        industry_vertical: registerForm.industry_vertical,
        plan_type: registerForm.plan_type
      });
      setAuth(data);
      toast('Jisajili imefanikiwa! / Registration successful!', 'success');
      closeAllModals();
      router.push('/onboarding');
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Uandikishaji umeshindwa. Jaribu tena.', 'error');
    } finally {
      setModalLoading(false);
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    // Simulate reset link sending
    setTimeout(() => {
      setModalLoading(false);
      toast('Kiungo cha kuweka upya neno la siri kimetumwa kwenye barua pepe yako!', 'success');
      setActiveModal('login');
    }, 1500);
  };

  const handleCheckoutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    
    if (checkoutPlan === 'free') {
      setTimeout(() => {
        setModalLoading(false);
        toast('Plan Bure imewezeshwa! / Free plan activated successfully.', 'success');
        closeAllModals();
        router.push('/dashboard');
      }, 1200);
      return;
    }

    try {
      const amount = checkoutPlan === 'growth' ? 75000 : 200000;
      if (token) {
        await api.post(
          '/api/v1/billing/top-up',
          { amount, payment_method: 'm_pesa', phone_number: mpesaPhone },
          token
        );
      }
      toast('M-Pesa STK push imetumwa! Tafadhali weka PIN kwenye simu yako kukamilisha malipo.', 'success');
      closeAllModals();
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Ombi la M-Pesa limeshindwa. Jaribu tena.', 'error');
    } finally {
      setModalLoading(false);
    }
  };

  // Toast notifications helper
  const handleFeatureNotice = (msg: string) => {
    toast(`${msg} inakuja hivi karibuni! / coming soon!`, 'info');
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-[#E2E8F0] font-sans selection:bg-[#10B981]/30 selection:text-white relative overflow-hidden flex flex-col">
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] rounded-full bg-[#10B981]/5 blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-[40%] right-[-10%] w-[500px] h-[500px] rounded-full bg-emerald-900/5 blur-[120px] pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] left-[20%] w-[600px] h-[600px] rounded-full bg-[#10B981]/3 blur-[150px] pointer-events-none z-0" />

      {/* Embedded style block for custom marquee and scrollbar CSS */}
      <style jsx global>{`
        @keyframes marquee {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 30s linear infinite;
        }
        .animate-marquee:hover {
          animation-play-state: paused;
        }
        /* Custom scrollbar for preview */
        .custom-scroll::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: #0f172a;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: #1e293b;
          border-radius: 4px;
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: #10b981;
        }
      `}</style>

      {/* Grid Pattern overlay for Hero */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0c1d18_1px,transparent_1px),linear-gradient(to_bottom,#0c1d18_1px,transparent_1px)] bg-[size:5rem_5rem] pointer-events-none opacity-40 z-0" />

      {/* Navigation Header */}
      <header className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between z-50">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#10B981] animate-pulse" />
          <span className="text-xl font-bold tracking-tight text-white flex items-center">
            SalesAgent<span className="text-[#10B981] font-extrabold ml-1">TZ</span>
          </span>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#94A3B8]">
          <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
          <a href="#stories" className="hover:text-white transition-colors">Stories</a>
        </nav>

        {/* Action Buttons */}
        <div className="hidden md:flex items-center gap-4">
          <button 
            onClick={() => setActiveModal('login')}
            className="text-sm font-semibold text-[#94A3B8] hover:text-white transition-colors focus:outline-none"
          >
            Ingia — Login
          </button>
          <Button 
            onClick={() => {
              setRegisterForm(prev => ({ ...prev, plan_type: 'free' }));
              setActiveModal('register');
            }}
            size="sm" 
            className="bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold px-4 py-2 transition-all hover:shadow-[0_0_15px_rgba(16,185,129,0.3)]"
          >
            Jaribu bure ↗
          </Button>
        </div>

        {/* Mobile Hamburger menu */}
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden text-[#94A3B8] hover:text-white focus:outline-none"
          aria-label="Toggle Menu"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </header>

      {/* Mobile Drawer menu */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-20 left-4 right-4 bg-[#0F172A]/95 backdrop-blur-md border border-[#1E293B] rounded-2xl p-6 flex flex-col gap-4 z-50 animate-in fade-in slide-in-from-top-5 duration-200">
          <a 
            href="#how-it-works" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-[#E2E8F0] py-2 border-b border-[#1E293B]"
          >
            How it works
          </a>
          <a 
            href="#features" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-[#E2E8F0] py-2 border-b border-[#1E293B]"
          >
            Features
          </a>
          <a 
            href="#pricing" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-[#E2E8F0] py-2 border-b border-[#1E293B]"
          >
            Pricing
          </a>
          <a 
            href="#stories" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-base font-medium text-[#E2E8F0] py-2 border-b border-[#1E293B]"
          >
            Stories
          </a>
          <div className="flex flex-col gap-3 pt-2">
            <button 
              onClick={() => {
                setMobileMenuOpen(false);
                setActiveModal('login');
              }} 
              className="text-center text-sm font-semibold text-[#94A3B8] py-2"
            >
              Ingia — Login
            </button>
            <Button 
              onClick={() => {
                setMobileMenuOpen(false);
                setRegisterForm(prev => ({ ...prev, plan_type: 'free' }));
                setActiveModal('register');
              }}
              className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold"
            >
              Jaribu bure
            </Button>
          </div>
        </div>
      )}

      {/* HERO SECTION */}
      <section className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-16 flex flex-col items-center justify-center text-center z-10">
        
        {/* Tanzanian pill badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] text-xs font-bold tracking-wider uppercase mb-8 shadow-sm">
          <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping" />
          AI Sales Agent — Built for Tanzania
        </div>

        {/* Big Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-[1.15] text-white">
          Pata wateja <span className="text-white">wapya.</span><br />
          <span className="text-[#10B981]">Kiotomatiki.</span> Every night.
        </h1>

        {/* Paragraph Description */}
        <p className="mt-8 text-base sm:text-lg text-[#94A3B8] max-w-2xl mx-auto leading-relaxed">
          Your AI agent finds leads, sends personalized WhatsApp messages in Swahili or English, qualifies replies, and builds your pipeline — while you sleep.
        </p>

        {/* Action Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
          <Button 
            onClick={() => {
              setRegisterForm(prev => ({ ...prev, plan_type: 'free' }));
              setActiveModal('register');
            }}
            size="lg" 
            className="w-full sm:w-auto bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-extrabold px-8 py-6 rounded-xl flex items-center justify-center gap-2 text-base transition-all hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
          >
            Anza bure — Start free
            <ArrowRight className="h-5 w-5" />
          </Button>
          <Button 
            onClick={() => setActiveModal('demo')}
            size="lg" 
            variant="outline" 
            className="w-full sm:w-auto bg-transparent border border-[#334155] text-white hover:bg-[#1E293B]/50 hover:border-[#475569] px-8 py-6 rounded-xl flex items-center justify-center gap-2 text-base transition-all"
          >
            <Play className="h-4.5 w-4.5 text-[#10B981] fill-[#10B981]" />
            Watch 90s demo
          </Button>
        </div>

        {/* Trust Indicators */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-3">
          <div className="flex -space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-teal-600 border-2 border-[#090D16] flex items-center justify-center text-[10px] font-bold text-white">JM</div>
            <div className="w-8 h-8 rounded-full bg-blue-600 border-2 border-[#090D16] flex items-center justify-center text-[10px] font-bold text-white">AK</div>
            <div className="w-8 h-8 rounded-full bg-yellow-600 border-2 border-[#090D16] flex items-center justify-center text-[10px] font-bold text-white">FA</div>
          </div>
          <p className="text-xs sm:text-sm text-[#64748B] font-medium">
            Trusted by growing businesses in <span className="text-[#94A3B8] font-semibold">Dar es Salaam, Mwanza & Arusha</span>
          </p>
        </div>
      </section>

      {/* METRICS SCROLLING MARQUEE */}
      <section className="relative w-full border-y border-[#1E293B] bg-[#0A0F1D]/50 py-5 overflow-hidden z-10">
        <div className="flex w-[200%] md:w-[150%] animate-marquee whitespace-nowrap gap-12 text-sm font-semibold tracking-wider text-[#94A3B8]">
          <div className="flex gap-12 items-center">
            <span className="flex items-center gap-2"><Globe2 className="h-4.5 w-4.5 text-[#10B981]" /> 11.4% Reply rate</span>
            <span className="text-[#334155]">•</span>
            <span>203 Active campaigns</span>
            <span className="text-[#334155]">•</span>
            <span className="text-white">830 BRELA verified leads</span>
            <span className="text-[#334155]">•</span>
            <span>18 Industries covered</span>
            <span className="text-[#334155]">•</span>
            <span>12 Cities reached</span>
            <span className="text-[#334155]">•</span>
            <span className="text-[#10B981]">1,240 Leads found today</span>
            <span className="text-[#334155]">•</span>
            <span>8,900 Messages sent</span>
            <span className="text-[#334155]">•</span>
            <span className="text-white">TZS 3.4M closed deals</span>
          </div>
          {/* Repeating identical block for infinite scroll */}
          <div className="flex gap-12 items-center">
            <span className="flex items-center gap-2"><Globe2 className="h-4.5 w-4.5 text-[#10B981]" /> 11.4% Reply rate</span>
            <span className="text-[#334155]">•</span>
            <span>203 Active campaigns</span>
            <span className="text-[#334155]">•</span>
            <span className="text-white">830 BRELA verified leads</span>
            <span className="text-[#334155]">•</span>
            <span>18 Industries covered</span>
            <span className="text-[#334155]">•</span>
            <span>12 Cities reached</span>
            <span className="text-[#334155]">•</span>
            <span className="text-[#10B981]">1,240 Leads found today</span>
            <span className="text-[#334155]">•</span>
            <span>8,900 Messages sent</span>
            <span className="text-[#334155]">•</span>
            <span className="text-white">TZS 3.4M closed deals</span>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS SECTION */}
      <section id="how-it-works" className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 z-10">
        
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <span className="text-xs font-bold text-[#10B981] tracking-wider uppercase">How it works</span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white">
            From zero to hot lead in 30 minutes
          </h2>
        </div>

        {/* 5-Step Process Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-stretch">
          
          {/* Step 1 */}
          <div className="relative rounded-2xl bg-[#0F172A]/70 border border-[#1E293B] p-6 flex flex-col justify-between overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
            <span className="absolute -top-6 -left-2 text-[8rem] font-extrabold text-[#1E293B]/25 select-none font-mono group-hover:text-[#10B981]/5 transition-colors">1</span>
            <div className="relative space-y-4 z-10">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/50 border border-[#10B981]/20 flex items-center justify-center text-[#10B981]">
                <MessageSquare className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-white">Describe your business</h3>
              <p className="text-xs text-[#94A3B8] leading-relaxed">
                Tell the AI who you are and who your ideal customer is. No technical setup. Just plain language.
              </p>
            </div>
            <div className="relative pt-6 text-[10px] font-bold text-[#10B981] flex items-center gap-1 z-10">
              2 min • Click to learn more <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative rounded-2xl bg-[#0F172A]/70 border border-[#1E293B] p-6 flex flex-col justify-between overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
            <span className="absolute -top-6 -left-2 text-[8rem] font-extrabold text-[#1E293B]/25 select-none font-mono group-hover:text-[#10B981]/5 transition-colors">2</span>
            <div className="relative space-y-4 z-10">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/50 border border-[#10B981]/20 flex items-center justify-center text-[#10B981]">
                <Search className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-white">Agent finds leads</h3>
              <p className="text-xs text-[#94A3B8] leading-relaxed">
                Scout Agent searches Google Maps and BRELA for verified businesses matching your criteria across Tanzania.
              </p>
            </div>
            <div className="relative pt-6 text-[10px] font-bold text-[#10B981] flex items-center gap-1 z-10">
              Auto 60s • Click to learn more <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative rounded-2xl bg-[#0F172A]/70 border border-[#1E293B] p-6 flex flex-col justify-between overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
            <span className="absolute -top-6 -left-2 text-[8rem] font-extrabold text-[#1E293B]/25 select-none font-mono group-hover:text-[#10B981]/5 transition-colors">3</span>
            <div className="relative space-y-4 z-10">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/50 border border-[#10B981]/20 flex items-center justify-center text-[#10B981]">
                <Languages className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-white">WhatsApp outreach</h3>
              <p className="text-xs text-[#94A3B8] leading-relaxed">
                Personalized messages in Swahili, English, or a mix — sent automatically to every lead at the right time.
              </p>
            </div>
            <div className="relative pt-6 text-[10px] font-bold text-[#10B981] flex items-center gap-1 z-10">
              24/7 auto • Click to learn more <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Step 4 */}
          <div className="relative rounded-2xl bg-[#0F172A]/70 border border-[#1E293B] p-6 flex flex-col justify-between overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
            <span className="absolute -top-6 -left-2 text-[8rem] font-extrabold text-[#1E293B]/25 select-none font-mono group-hover:text-[#10B981]/5 transition-colors">4</span>
            <div className="relative space-y-4 z-10">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/50 border border-[#10B981]/20 flex items-center justify-center text-[#10B981]">
                <Check className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-white">Replies qualified</h3>
              <p className="text-xs text-[#94A3B8] leading-relaxed">
                AI reads every response, detects intent and objections, and decides who&apos;s hot, warm, or cold automatically.
              </p>
            </div>
            <div className="relative pt-6 text-[10px] font-bold text-[#10B981] flex items-center gap-1 z-10">
              Instant • Click to learn more <ArrowRight className="h-3 w-3" />
            </div>
          </div>

          {/* Step 5 */}
          <div className="relative rounded-2xl bg-[#0F172A]/70 border border-[#1E293B] p-6 flex flex-col justify-between overflow-hidden group hover:border-[#10B981]/30 transition-all duration-300">
            <span className="absolute -top-6 -left-2 text-[8rem] font-extrabold text-[#1E293B]/25 select-none font-mono group-hover:text-[#10B981]/5 transition-colors">5</span>
            <div className="relative space-y-4 z-10">
              <div className="w-10 h-10 rounded-xl bg-emerald-950/50 border border-[#10B981]/20 flex items-center justify-center text-[#10B981]">
                <CreditCard className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-white">You close the deal</h3>
              <p className="text-xs text-[#94A3B8] leading-relaxed">
                Hot leads appear in your Kanban pipeline. Your only job is to pick up the phone and close. The AI did the rest.
              </p>
            </div>
            <div className="relative pt-6 text-[10px] font-bold text-[#10B981] flex items-center gap-1 z-10">
              Your moment • Click to learn more <ArrowRight className="h-3 w-3" />
            </div>
          </div>

        </div>
      </section>

      {/* LIVE PREVIEW SECTION */}
      <section id="preview" className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Content side */}
          <div className="lg:col-span-5 space-y-6">
            <span className="text-xs font-bold text-[#10B981] tracking-wider uppercase">Live Preview</span>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
              Watch your agent work in real time
            </h2>
            <p className="text-[#94A3B8] text-sm leading-relaxed">
              This is an actual conversation your AI agent would have on your behalf - in fluent Swahili - without you typing a single word.
            </p>
            
            <ul className="space-y-4 pt-4">
              <li className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-950 flex items-center justify-center border border-[#10B981]/30 shrink-0 text-[#10B981]">
                  <Check className="h-3.5 w-3.5" />
                </div>
                <span className="text-sm text-[#E2E8F0] font-medium">Personalized per business - name, industry, location</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-950 flex items-center justify-center border border-[#10B981]/30 shrink-0 text-[#10B981]">
                  <Check className="h-3.5 w-3.5" />
                </div>
                <span className="text-sm text-[#E2E8F0] font-medium">Handles objections, follow-ups, and scheduling</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-emerald-950 flex items-center justify-center border border-[#10B981]/30 shrink-0 text-[#10B981]">
                  <Check className="h-3.5 w-3.5" />
                </div>
                <span className="text-sm text-[#E2E8F0] font-medium">Notifies you only when a lead is truly interested</span>
              </li>
            </ul>
          </div>

          {/* Interactive WhatsApp Mockup side */}
          <div className="lg:col-span-7 flex justify-center">
            <div className="w-full max-w-[420px] rounded-[32px] border-8 border-[#1E293B] bg-[#090D16] shadow-2xl overflow-hidden aspect-[9/16] flex flex-col relative">
              
              {/* WhatsApp Header */}
              <div className="bg-[#202c33] px-4 py-3 flex items-center justify-between border-b border-[#334155]/20">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-[#10B981] flex items-center justify-center text-xs font-bold text-[#090D16]">
                    SA
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">SalesAgent - Jua Kali Co.</h4>
                    <span className="text-[10px] text-[#10B981] font-medium">online</span>
                  </div>
                </div>
                <div className="flex gap-4 text-[#94A3B8]">
                  {/* Phone icon */}
                  <svg className="w-4.5 h-4.5" fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79a15.15 15.15 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.11-.27 11.36 11.36 0 0 0 3.58.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11.36 11.36 0 0 0 .57 3.58 1 1 0 0 1-.27 1.1l-2.18 2.1z"/></svg>
                  {/* Video icon */}
                  <svg className="w-4.5 h-4.5" fill="currentColor" viewBox="0 0 24 24"><path d="M17 10.5V7a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3.5l4 4v-11l-4 4z"/></svg>
                </div>
              </div>

              {/* Chat Messages Body */}
              <div className="flex-1 bg-[#0b141a] p-4 flex flex-col gap-3.5 overflow-y-auto custom-scroll">
                
                {/* Background WhatsApp wallpaper overlay pattern */}
                <div className="absolute inset-0 bg-[radial-gradient(#10b981_0.5px,transparent_0.5px)] [background-size:16px_16px] opacity-[0.03] pointer-events-none" />

                {chatMessages.filter(Boolean).map((msg, index) => (
                  <div 
                    key={index}
                    className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs relative animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                      msg.sender === 'agent' 
                        ? 'self-end bg-[#005c4b] text-white rounded-tr-none' 
                        : 'self-start bg-[#202c33] text-[#E2E8F0] rounded-tl-none'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    <span className="block text-[9px] text-right mt-1.5 text-slate-400 select-none">{msg.time}</span>
                  </div>
                ))}

                {/* Simulated Typing Indicator */}
                {isTyping && (
                  <div className="self-start bg-[#202c33] rounded-2xl rounded-tl-none px-3.5 py-2 text-xs flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-bounce" />
                  </div>
                )}

              </div>

              {/* Chat Input Bar */}
              <div className="bg-[#202c33] px-3 py-2 flex items-center gap-3 border-t border-[#334155]/20">
                <div className="flex-1 bg-[#2a3942] rounded-full px-4 py-2 text-xs text-slate-500 select-none">
                  Write a message...
                </div>
                <div className="w-8 h-8 rounded-full bg-[#00a884] flex items-center justify-center text-white shrink-0">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
                </div>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* FEATURES GRID SECTION */}
      <section id="features" className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 z-10">
        
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <span className="text-xs font-bold text-[#10B981] tracking-wider uppercase">Features</span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white max-w-3xl mx-auto leading-tight">
            Everything Tanzania&apos;s sales teams need. Nothing they don&apos;t.
          </h2>
        </div>

        {/* 6-Grid Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Lead Discovery
              </span>
              <h3 className="text-lg font-bold text-white">Google Maps + BRELA Scout</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Finds real, verified businesses across Tanzania - with ratings, contact details, and registration status pulled automatically.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              50+ leads found per search • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Card 2 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Outreach
              </span>
              <h3 className="text-lg font-bold text-white">Swahili-first messaging</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                AI writes culturally appropriate outreach in Swahili, English, or code-switched Swahili-English - the way Tanzanians actually communicate.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              3x higher reply rate • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Card 3 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Pipeline
              </span>
              <h3 className="text-lg font-bold text-white">Kanban deal board</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Automatically moves leads through stages as they respond. See your pipeline in real time - no manual data entry, ever.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              100% automated stage updates • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Card 4 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Qualification
              </span>
              <h3 className="text-lg font-bold text-white">AI reply intelligence</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Detects interest, objections, pricing questions, and competitor mentions. Routes hot leads to you immediately, handles cold leads automatically.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              Smart intent detection • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Card 5 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Payments
              </span>
              <h3 className="text-lg font-bold text-white">M-Pesa native billing</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Pay your subscription and receive client payments via M-Pesa Lipa Na. No international card, no dollar conversions.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              TZS local payments only • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* Card 6 */}
          <div className="rounded-2xl bg-[#0F172A]/80 border border-[#1E293B] p-6 hover:border-[#10B981]/30 hover:translate-y-[-2px] transition-all duration-300 flex flex-col justify-between shadow-lg">
            <div className="space-y-4">
              <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] tracking-wider uppercase">
                Multi-Tenant
              </span>
              <h3 className="text-lg font-bold text-white">Agency-ready</h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Run campaigns for multiple clients under one login. Each client gets their own isolated workspace, pipeline, and WhatsApp number.
              </p>
            </div>
            <div className="pt-6 flex items-center text-xs font-bold text-[#10B981] gap-1 cursor-pointer">
              ∞ client accounts • Click to explore <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

        </div>
      </section>

      {/* STORIES / TESTIMONIALS SECTION */}
      <section id="stories" className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 z-10">
        
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <span className="text-xs font-bold text-[#10B981] tracking-wider uppercase font-mono">Stories</span>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white max-w-2xl mx-auto leading-tight">
            Wafanyabiashara wanaotumia SalesAgentTZ
          </h2>
        </div>

        {/* Animated Testimonials Carousel */}
        <div className="relative w-full overflow-hidden mt-8 max-w-full">
          {/* Gradient Edges */}
          <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-[#090D16] to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-[#090D16] to-transparent z-10 pointer-events-none" />
          
          <div className="flex w-[300%] md:w-[250%] animate-marquee whitespace-nowrap gap-6 hover:[animation-play-state:paused]">
            {/* Carousel Item Group 1 */}
            <div className="flex gap-6 items-center shrink-0">
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Niliweka kampeni usiku wa Ijumaa. Asubuhi ya Jumamosi nilikuwa na mazungumzo 4 na wateja wapya. Siwezi kuamini.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-teal-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">JM</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Juma Mwamba</h4>
                    <span className="text-xs text-[#64748B]">Real Estate - Dar es Salaam</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;My sales team was spending 6 hours a day on cold outreach. Now the agent handles all of it and they only call warm leads. Revenue is up 40%.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-blue-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">AK</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Amina Khalid</h4>
                    <span className="text-xs text-[#64748B]">Insurance Agency - Arusha</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Tunasaidia makampuni 8 sasa hivi. Kila kampuni ina mfumo wake wa mazungumzo. Ni kama kuwa na wafanyakazi 8 ambao hawachoki.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-yellow-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">FA</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Farida Ally</h4>
                    <span className="text-xs text-[#64748B]">Marketing Agency - Mwanza</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Agentic AI is the future. SalesAgent TZ localized it perfectly for the East African market. We don't need expensive call centers anymore.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-purple-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">BM</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Baraka Msuya</h4>
                    <span className="text-xs text-[#64748B]">Logistics - Dodoma</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Mwanzo nilidhani ni ngumu kutumia, lakini mfumo huu unajifanyia kila kitu. Wateja wanafurahia jinsi ninavyowajibu kwa haraka kupitia WhatsApp.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-orange-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">NN</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Neema Nyerere</h4>
                    <span className="text-xs text-[#64748B]">Retail - Zanzibar</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Closing deals has never been this smooth. The AI brings them directly to the qualification stage, and my SDRs just take over from there.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-rose-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">DK</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Daniel Kibo</h4>
                    <span className="text-xs text-[#64748B]">SaaS Founder - Nairobi</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Kijani AI imerahisisha sana kazi yetu. Sasa tunaweza kufikia wateja wengi zaidi kwa muda mfupi bila kupoteza ubora wa huduma.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-indigo-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">ST</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Salum Tiba</h4>
                    <span className="text-xs text-[#64748B]">Agribusiness - Morogoro</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;We replaced three different tools with this one platform. The M-Pesa billing makes it incredibly accessible for local SMEs.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-cyan-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">CJ</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Catherine John</h4>
                    <span className="text-xs text-[#64748B]">Consulting - Dar es Salaam</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Carousel Item Group 2 (Duplicate for Infinite Scroll) */}
            <div className="flex gap-6 items-center shrink-0">
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Niliweka kampeni usiku wa Ijumaa. Asubuhi ya Jumamosi nilikuwa na mazungumzo 4 na wateja wapya. Siwezi kuamini.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-teal-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">JM</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Juma Mwamba</h4>
                    <span className="text-xs text-[#64748B]">Real Estate - Dar es Salaam</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;My sales team was spending 6 hours a day on cold outreach. Now the agent handles all of it and they only call warm leads. Revenue is up 40%.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-blue-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">AK</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Amina Khalid</h4>
                    <span className="text-xs text-[#64748B]">Insurance Agency - Arusha</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Tunasaidia makampuni 8 sasa hivi. Kila kampuni ina mfumo wake wa mazungumzo. Ni kama kuwa na wafanyakazi 8 ambao hawachoki.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-yellow-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">FA</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Farida Ally</h4>
                    <span className="text-xs text-[#64748B]">Marketing Agency - Mwanza</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Agentic AI is the future. SalesAgent TZ localized it perfectly for the East African market. We don't need expensive call centers anymore.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-purple-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">BM</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Baraka Msuya</h4>
                    <span className="text-xs text-[#64748B]">Logistics - Dodoma</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Mwanzo nilidhani ni ngumu kutumia, lakini mfumo huu unajifanyia kila kitu. Wateja wanafurahia jinsi ninavyowajibu kwa haraka kupitia WhatsApp.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-orange-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">NN</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Neema Nyerere</h4>
                    <span className="text-xs text-[#64748B]">Retail - Zanzibar</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Closing deals has never been this smooth. The AI brings them directly to the qualification stage, and my SDRs just take over from there.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-rose-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">DK</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Daniel Kibo</h4>
                    <span className="text-xs text-[#64748B]">SaaS Founder - Nairobi</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;Kijani AI imerahisisha sana kazi yetu. Sasa tunaweza kufikia wateja wengi zaidi kwa muda mfupi bila kupoteza ubora wa huduma.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-indigo-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">ST</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Salum Tiba</h4>
                    <span className="text-xs text-[#64748B]">Agribusiness - Morogoro</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-[#0F172A]/60 border border-[#1E293B] p-7 flex flex-col justify-between shadow-xl transition-all duration-300 hover:border-[#10B981]/20 w-[350px] h-[280px] whitespace-normal">
                <div className="space-y-6">
                  <div className="flex gap-1 text-[#10B981]">{[...Array(5)].map((_, i) => <Star key={i} className="h-4 w-4 fill-current" />)}</div>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed italic line-clamp-4">
                    &quot;We replaced three different tools with this one platform. The M-Pesa billing makes it incredibly accessible for local SMEs.&quot;
                  </p>
                </div>
                <div className="pt-6 flex items-center gap-3.5 mt-auto">
                  <div className="w-10 h-10 rounded-full bg-cyan-600/80 text-white flex items-center justify-center font-bold text-sm shrink-0">CJ</div>
                  <div>
                    <h4 className="text-sm font-bold text-white leading-none">Catherine John</h4>
                    <span className="text-xs text-[#64748B]">Consulting - Dar es Salaam</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* INTEGRATED MINI PRICING SECTION */}
      <section id="pricing" className="relative w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 z-10">
        <div className="rounded-3xl bg-gradient-to-br from-[#0F172A] to-[#122b22] border border-[#10B981]/20 p-8 sm:p-12 shadow-[0_0_50px_rgba(16,185,129,0.05)]">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Left Header and CTA */}
            <div className="lg:col-span-5 space-y-6">
              <h3 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
                Simple pricing.<br />Pay with M-Pesa.
              </h3>
              <p className="text-sm text-[#94A3B8] leading-relaxed">
                Start free. Upgrade when your pipeline fills up. No international credit card required.
              </p>
              <div className="pt-2">
                <Button 
                  onClick={() => {
                    setCheckoutPlan('free');
                    setActiveModal('checkout');
                  }}
                  className="bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-extrabold px-6 py-5 rounded-xl text-sm flex items-center gap-2"
                >
                  Anza bure — no credit card
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Right Plan overview cards */}
            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-4">
              
              {/* Bure */}
              <div 
                onClick={() => {
                  setCheckoutPlan('free');
                  setActiveModal('checkout');
                }}
                className="rounded-xl bg-[#090D16]/90 border border-[#1E293B] p-5 space-y-4 shadow-md hover:border-[#10B981]/30 cursor-pointer transition-all hover:scale-[1.02]"
              >
                <div>
                  <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider block">Bure • Free</span>
                  <h4 className="text-xl font-black text-white mt-1">TZS 0</h4>
                </div>
                <div className="text-[11px] text-[#94A3B8] space-y-2">
                  <p className="font-semibold text-white">20 leads/mo</p>
                  <p>1 active campaign</p>
                  <p className="text-emerald-500 font-medium pt-1">Forever free</p>
                </div>
              </div>

              {/* Biashara */}
              <div 
                onClick={() => {
                  setCheckoutPlan('growth');
                  setActiveModal('checkout');
                }}
                className="rounded-xl bg-[#090D16]/95 border-2 border-[#10B981] p-5 space-y-4 shadow-[0_0_15px_rgba(16,185,129,0.1)] relative cursor-pointer hover:scale-[1.02] transition-all"
              >
                <div className="absolute top-0 right-4 transform -translate-y-1/2 bg-[#10B981] text-[#090D16] text-[8px] font-bold px-2 py-0.5 rounded-full uppercase">
                  Popular
                </div>
                <div>
                  <span className="text-[10px] font-bold text-[#10B981] uppercase tracking-wider block">Biashara • Growth</span>
                  <h4 className="text-xl font-black text-white mt-1">TZS 75K</h4>
                </div>
                <div className="text-[11px] text-[#94A3B8] space-y-2">
                  <p className="font-semibold text-white">200 leads/mo</p>
                  <p>5 active campaigns</p>
                  <p className="text-emerald-500 font-medium pt-1">Most popular</p>
                </div>
              </div>

              {/* Shirika */}
              <div 
                onClick={() => {
                  setCheckoutPlan('agency');
                  setActiveModal('checkout');
                }}
                className="rounded-xl bg-[#090D16]/90 border border-[#1E293B] p-5 space-y-4 shadow-md hover:border-[#10B981]/30 cursor-pointer transition-all hover:scale-[1.02]"
              >
                <div>
                  <span className="text-[10px] font-bold text-[#64748B] uppercase tracking-wider block">Shirika • Agency</span>
                  <h4 className="text-xl font-black text-white mt-1">TZS 200K</h4>
                </div>
                <div className="text-[11px] text-[#94A3B8] space-y-2">
                  <p className="font-semibold text-white">1,000 leads/mo</p>
                  <p>Unlimited campaigns</p>
                  <p className="text-emerald-500 font-medium pt-1">For agencies</p>
                </div>
              </div>

            </div>

          </div>
        </div>
      </section>

      {/* FOOTER CTA & LIPAA NOTE */}
      <section className="relative w-full max-w-4xl mx-auto px-4 py-8 text-center z-10">
        <h3 className="text-2xl sm:text-3xl font-extrabold text-white">Anza leo. Lipa baadaye.</h3>
        <p className="text-xs text-[#94A3B8] mt-2">
          • Lipa kwa M-Pesa • Pay via M-Pesa when you upgrade
        </p>
      </section>

      {/* FOOTER */}
      <footer className="relative w-full border-t border-[#1E293B] bg-[#070A11] py-12 mt-auto z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          
          {/* Logo and tagline */}
          <div className="flex flex-col items-center md:items-start gap-2 text-center md:text-left">
            <span className="text-base font-bold text-white">
              SalesAgent<span className="text-[#10B981]">TZ</span>
            </span>
            <span className="text-xs text-[#64748B]">
              AI outbound sales for Tanzania
            </span>
          </div>

          {/* Links */}
          <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs font-semibold text-[#94A3B8]">
            <button onClick={() => handleFeatureNotice('Privacy')} className="hover:text-white transition-colors focus:outline-none">Privacy</button>
            <button onClick={() => handleFeatureNotice('Terms')} className="hover:text-white transition-colors focus:outline-none">Terms</button>
            <a href="https://wa.me/918487059610?text=Habari!%20I%20need%20support%20with%20SalesAgent%20TZ" target="_blank" className="hover:text-white transition-colors">WhatsApp Support</a>
            <button onClick={() => handleFeatureNotice('PDPA Compliance')} className="hover:text-white transition-colors focus:outline-none">PDPA Compliance</button>
          </div>

          {/* Copyright */}
          <div className="text-xs text-[#64748B] text-center md:text-right">
            © 2025 SalesAgentTZ — Dar es Salaam
          </div>

        </div>
      </footer>

      {/* ==================================== MODAL DIALOGS ==================================== */}
      
      {activeModal && (
        <div 
          onClick={closeAllModals}
          className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200"
        >
          {/* Modal Container */}
          <div 
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-[#0F172A] border border-[#334155] rounded-3xl p-6 sm:p-8 relative shadow-[0_0_50px_rgba(16,185,129,0.08)] animate-in zoom-in-95 duration-200"
          >
            
            {/* Close Button */}
            <button 
              onClick={closeAllModals}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-1"
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </button>

            {/* LOGIN MODAL */}
            {activeModal === 'login' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-black text-white flex items-center justify-center gap-2">
                    <ShieldCheck className="h-6 w-6 text-[#10B981]" />
                    Ingia Kijani AI
                  </h3>
                  <p className="text-xs text-[#94A3B8] mt-1">Ingiza taarifa zako za kuingia kwenye akaunti yako</p>
                </div>

                <form onSubmit={handleLoginSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Barua pepe / Email</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="email" 
                        required
                        value={loginForm.email}
                        onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                        placeholder="mfano@kampuni.co.tz"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                      <label className="text-xs font-bold text-[#E2E8F0]">Neno la Siri / Password</label>
                      <button 
                        type="button"
                        onClick={() => setActiveModal('forgot_password')}
                        className="text-[10px] text-[#10B981] hover:underline focus:outline-none"
                      >
                        Forgot password?
                      </button>
                    </div>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="password" 
                        required
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                        placeholder="••••••••"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Slug ya Kampuni (Optional)</label>
                    <input 
                      type="text" 
                      value={loginForm.tenantSlug}
                      onChange={(e) => setLoginForm({ ...loginForm, tenantSlug: e.target.value })}
                      placeholder="kampuni-yako"
                      className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                    />
                  </div>

                  <Button 
                    type="submit" 
                    disabled={modalLoading}
                    className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold py-3 mt-2 flex items-center justify-center gap-2"
                  >
                    {modalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Ingia hapa'}
                  </Button>
                </form>

                <div className="relative flex items-center justify-center">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-[#1E293B]"></div>
                  </div>
                  <span className="relative bg-[#0F172A] px-3 text-[10px] text-[#64748B] uppercase font-bold tracking-wider">Au ingia kwa</span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button 
                    onClick={() => handleFeatureNotice('WhatsApp Login')}
                    className="flex items-center justify-center gap-2 py-2 px-3 border border-[#1E293B] bg-[#090D16] rounded-xl text-xs font-semibold hover:border-emerald-500/30 transition-all text-[#E2E8F0]"
                  >
                    <MessageCircle className="w-4.5 h-4.5 text-[#10B981] fill-current" />
                    WhatsApp
                  </button>
                  <button 
                    onClick={() => handleFeatureNotice('Google Login')}
                    className="flex items-center justify-center gap-2 py-2 px-3 border border-[#1E293B] bg-[#090D16] rounded-xl text-xs font-semibold hover:border-emerald-500/30 transition-all text-[#E2E8F0]"
                  >
                    <Globe2 className="w-4.5 h-4.5 text-[#10B981]" />
                    Google
                  </button>
                </div>

                <p className="text-center text-xs text-[#94A3B8]">
                  Huna akaunti?{' '}
                  <button 
                    onClick={() => {
                      setRegisterForm(prev => ({ ...prev, plan_type: 'free' }));
                      setActiveModal('register');
                    }}
                    className="text-[#10B981] hover:underline font-semibold focus:outline-none"
                  >
                    Jisajili bure hapa
                  </button>
                </p>
              </div>
            )}

            {/* REGISTER MODAL */}
            {activeModal === 'register' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-black text-white flex items-center justify-center gap-2">
                    Jisajili Kijani AI
                  </h3>
                  <p className="text-xs text-[#94A3B8] mt-1">Anza kujenga bomba lako la mauzo sasa hivi</p>
                </div>

                <form onSubmit={handleRegisterSubmit} className="space-y-4 max-h-[380px] overflow-y-auto pr-1 custom-scroll">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Jina la Biashara / Company Name</label>
                    <div className="relative">
                      <Building className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="text" 
                        required
                        value={registerForm.company_name}
                        onChange={(e) => setRegisterForm({ ...registerForm, company_name: e.target.value })}
                        placeholder="mfano: Jua Kali Co."
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Barua pepe / Email</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="email" 
                        required
                        value={registerForm.email}
                        onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                        placeholder="mauzo@kampuni.co.tz"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Namba ya Simu / Phone</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="text" 
                        required
                        value={registerForm.phone}
                        onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                        placeholder="+255 799 999 999"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Neno la Siri / Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="password" 
                        required
                        value={registerForm.password}
                        onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                        placeholder="••••••••"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Sekta ya Biashara / Industry</label>
                    <input 
                      type="text" 
                      value={registerForm.industry_vertical}
                      onChange={(e) => setRegisterForm({ ...registerForm, industry_vertical: e.target.value })}
                      placeholder="mfano: Ujenzi, Vipodozi, Kilimo"
                      className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                    />
                  </div>

                  <Button 
                    type="submit" 
                    disabled={modalLoading}
                    className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold py-3 mt-2 flex items-center justify-center gap-2"
                  >
                    {modalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Jisajili bure'}
                  </Button>
                </form>

                <p className="text-center text-xs text-[#94A3B8]">
                  Tayari una akaunti?{' '}
                  <button 
                    onClick={() => setActiveModal('login')}
                    className="text-[#10B981] hover:underline font-semibold focus:outline-none"
                  >
                    Ingia hapa
                  </button>
                </p>
              </div>
            )}

            {/* FORGOT PASSWORD MODAL */}
            {activeModal === 'forgot_password' && (
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-2xl font-black text-white">Weka Upya Siri</h3>
                  <p className="text-xs text-[#94A3B8] mt-1">Weka barua pepe yako ili kupata kiungo cha kubadilisha neno la siri</p>
                </div>

                <form onSubmit={handleForgotSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-[#E2E8F0]">Barua pepe / Email</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                      <input 
                        type="email" 
                        required
                        value={resetEmail}
                        onChange={(e) => setResetEmail(e.target.value)}
                        placeholder="mfano@kampuni.co.tz"
                        className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                      />
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    disabled={modalLoading}
                    className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold py-3 flex items-center justify-center gap-2"
                  >
                    {modalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Tuma ombi la kuweka upya'}
                  </Button>
                </form>

                <div className="text-center pt-2">
                  <button 
                    onClick={() => setActiveModal('login')}
                    className="text-xs text-[#10B981] hover:underline font-semibold focus:outline-none"
                  >
                    Rudi kwenye Login
                  </button>
                </div>
              </div>
            )}

            {/* DEMO MODAL */}
            {activeModal === 'demo' && (
              <div className="space-y-4">
                <div className="text-center">
                  <h3 className="text-lg font-bold text-white">SalesAgent TZ Walkthrough</h3>
                  <p className="text-xs text-[#94A3B8]">Simu fupi ya sekunde 90 kuona jinsi wakala wanavyofanya kazi</p>
                </div>

                <div className="overflow-hidden rounded-xl border border-[#334155]/50 bg-black">
                  <iframe 
                    className="w-full aspect-video"
                    src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
                    title="SalesAgent TZ demo"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowFullScreen
                  />
                </div>
                <p className="text-[10px] text-center text-[#64748B]">MVP: unaweza kuweka Loom au YouTube embed URL yako hapa kwenye uzalishaji.</p>
              </div>
            )}

            {/* CHECKOUT MODAL */}
            {activeModal === 'checkout' && (
              <div className="space-y-6">
                <div className="text-center">
                  <span className="text-[10px] font-bold text-[#10B981] uppercase tracking-wider block">Checkout</span>
                  <h3 className="text-2xl font-black text-white capitalize mt-1">
                    Plan {checkoutPlan}
                  </h3>
                  <p className="text-xs text-[#94A3B8] mt-1">
                    {checkoutPlan === 'free' && 'TZS 0 — 20 leads/month, 1 campaign'}
                    {checkoutPlan === 'growth' && 'TZS 75,000 / month — 200 leads/month'}
                    {checkoutPlan === 'agency' && 'TZS 200,000 / month — 1,000 leads/month'}
                  </p>
                </div>

                <form onSubmit={handleCheckoutSubmit} className="space-y-4">
                  {checkoutPlan !== 'free' ? (
                    <>
                      <div className="bg-[#12221b]/40 border border-[#10B981]/20 rounded-xl p-4 flex gap-3 text-xs text-[#94A3B8] items-start">
                        <MessageCircle className="h-5 w-5 text-[#10B981] shrink-0 mt-0.5" />
                        <p>
                          Lipa kwa urahisi kutumia <strong className="text-white">M-Pesa</strong>. Ombi la malipo (STK Push) litatokea kwenye simu yako ukiandika namba hapa chini.
                        </p>
                      </div>

                      <div className="space-y-1.5">
                        <label className="text-xs font-bold text-[#E2E8F0]">Namba ya Simu ya M-Pesa</label>
                        <div className="relative">
                          <Smartphone className="absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                          <input 
                            type="text" 
                            required
                            value={mpesaPhone}
                            onChange={(e) => setMpesaPhone(e.target.value)}
                            placeholder="+255 7XX XXX XXX"
                            className="w-full bg-[#090D16] border border-[#1E293B] rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#10B981]/50 text-white placeholder-slate-700"
                          />
                        </div>
                      </div>

                      <Button 
                        type="submit" 
                        disabled={modalLoading}
                        className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold py-3 flex items-center justify-center gap-2"
                      >
                        {modalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Lipa kwa M-Pesa ↗'}
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="bg-[#1e293b]/30 rounded-xl p-4 text-xs text-[#94A3B8] text-center">
                        Hakuna kadi au malipo yanayohitajika kuanza. Akaunti yako itakua na kiasi cha leads 20 mara moja.
                      </div>
                      
                      <Button 
                        type="submit" 
                        disabled={modalLoading}
                        className="w-full bg-[#10B981] hover:bg-[#0d9668] text-[#090D16] font-bold py-3 flex items-center justify-center gap-2"
                      >
                        {modalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Activate free plan'}
                      </Button>
                    </>
                  )}
                </form>

                <p className="text-[10px] text-center text-[#64748B]">MVP: malipo ya mfano. Toleo la uzalishaji linaunganishwa na Vodacom M-Pesa API.</p>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}

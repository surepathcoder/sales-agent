'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useWhatsAppQr } from '@/hooks/useWhatsApp';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/auth';
import { useToast } from '@/components/ui/toast';
import { 
  Sparkles, 
  MessageSquare, 
  Loader2, 
  CheckCircle2, 
  Search, 
  MapPin, 
  UserCheck, 
  ArrowRight,
  TrendingUp
} from 'lucide-react';

const STEPS = [
  { id: 'welcome', title: 'Karibu!', titleEn: 'Welcome' },
  { id: 'describe', title: 'Biashara Yako', titleEn: 'Describe Business' },
  { id: 'whatsapp', title: 'Unganisha WhatsApp', titleEn: 'Link WhatsApp' },
  { id: 'planning', title: 'Wakala Wanaandaa', titleEn: 'Agents At Work' },
  { id: 'magic', title: 'Matokeo Kwanza!', titleEn: 'Magic Moment' },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [description, setDescription] = useState('');
  const [agentProgress, setAgentProgress] = useState(0);
  const [agentLogs, setAgentLogs] = useState<string[]>([]);
  const [isFinishing, setIsFinishing] = useState(false);
  const token = useAuthStore((s) => s.accessToken);
  const router = useRouter();
  const { toast } = useToast();
  const { data: wa } = useWhatsAppQr();

  // Agent coordination simulation on Step 4 (Index 3)
  useEffect(() => {
    if (step === 3) {
      setAgentProgress(0);
      setAgentLogs([]);
      
      const logs = [
        "[Scout Agent] Uchambuzi wa maelezo yako umeanza / Analyzing your business details...",
        "[Scout Agent] Tunatafuta wateja kwenye Google Maps / Searching Google Maps for matches in Dar es Salaam...",
        "[Researcher Agent] Tunakagua tovuti za makampuni yaliyopatikana / Reviewing discovered business websites...",
        "[Researcher Agent] Tunatafuta viongozi wa ununuzi na mawasiliano / Scraping decision maker roles...",
        "[Outreach Agent] Tunaandaa ujumbe maalum wa WhatsApp wa Kiswahili na Kiingereza / Drafting Swahili-English outreach copy..."
      ];

      let logIndex = 0;
      const logInterval = setInterval(() => {
        if (logIndex < logs.length) {
          setAgentLogs(prev => [...prev, logs[logIndex]]);
          setAgentProgress(prev => Math.min(prev + 20, 100));
          logIndex++;
        } else {
          clearInterval(logInterval);
          // Auto transition to magic moment step after logs finish
          setTimeout(() => {
            setStep(4);
          }, 1000);
        }
      }, 1200);

      return () => clearInterval(logInterval);
    }
  }, [step]);

  // Tanzanian-centric mock leads generator for step 5
  const getLeads = () => {
    const descLower = description.toLowerCase();
    if (
      descLower.includes('ujenzi') || 
      descLower.includes('construction') || 
      descLower.includes('hardware') || 
      descLower.includes('vifaa') ||
      descLower.includes('cement') ||
      descLower.includes('nondo')
    ) {
      return [
        {
          company: "Bakhresa Construction Ltd",
          location: "Mikocheni, Dar es Salaam",
          contact: "John Massawe (Project Director)",
          pitch: "Habari John! Niliona miradi yenu mipya ya makazi Mikocheni. Kijani tunasambaza saruji na nondo zenye viwango vya juu kwa bei ya jumla na usafiri wa bure hadi saiti. Tungependa kusaidia kuzuia ucheleweshaji wa vifaa kwenye mradi wenu ujao. Tunaweza kuongea kidogo leo?"
        },
        {
          company: "Dar Civil Engineering",
          location: "Kurasini, Dar es Salaam",
          contact: "Mariam Juma (Procurement Officer)",
          pitch: "Habari Mariam, natumai upo vizuri. Nimeona kuwa mnafanya miradi ya miundombinu Dar. Kijani tunatoa vifaa vya ujenzi kwa mikataba rahisi ya malipo ya baadae (credit terms) kwa wakandarasi wa ndani. Ningependa kukutumia catalogue yetu ya bei kupitia WhatsApp. Je, hii ni namba yako sahihi?"
        },
        {
          company: "Mwanza Builders Depot",
          location: "Nyamagana, Mwanza",
          contact: "Peter Aloyce (Operations Manager)",
          pitch: "Habari Peter, niliona kuwa mnaongeza wigo wa miradi Mwanza. Sisi tunatoa huduma ya kusambaza kokoto na mchanga wa ujenzi kwa bei nafuu sana. Tunaweza kupanga simu fupi ya sekunde 30 leo kuona kama tunaweza kushirikiana?"
        }
      ];
    } else if (
      descLower.includes('rembo') || 
      descLower.includes('beauty') || 
      descLower.includes('salon') || 
      descLower.includes('saluni') || 
      descLower.includes('vipodozi') ||
      descLower.includes('spa')
    ) {
      return [
        {
          company: "Glitz & Glam Salon",
          location: "Masaki, Dar es Salaam",
          contact: "Sarah Kessy (Owner)",
          pitch: "Habari Sarah! Napenda sana kazi zenu za makeup na nywele mnavyopost Instagram. Sisi ni wasambazaji wakuu wa bidhaa asilia za nywele na ngozi kutoka Ulaya kwa bei ya jumla. Tungependa kuwapa punguzo la 15% kwenye oda yenu ya kwanza. Naweza kukutumia picha za bidhaa zetu hapa WhatsApp?"
        },
        {
          company: "Afro Hair Clinic",
          location: "Sinza, Dar es Salaam",
          contact: "Doreen Peter (Spa Manager)",
          pitch: "Habari Doreen, natumai siku yako inaenda vizuri. Nimeona kuwa mnasambaza bidhaa za nywele asilia Sinza. Kijani tuna vipodozi vyenye ubora wa kimataifa na tunatoa mafunzo ya bure kwa ma-stylist wenu jinsi ya kuvitumia. Tunaweza kuongea kidogo leo kuona jinsi ya kuongeza kipato cha saluni yenu?"
        },
        {
          company: "Mwanza Beauty Spa",
          location: "Rock City, Mwanza",
          contact: "Grace Lema (Operations Director)",
          pitch: "Habari Grace! Hongera kwa huduma nzuri za spa Mwanza. Sisi tunatoa mafuta ya massage na bidhaa za facial za jumla zenye viwango vya juu. Ningependa kukutumia bei zetu tuone kama tunaweza kufanya kazi pamoja. Je, naweza kukutumia leo?"
        }
      ];
    } else {
      return [
        {
          company: "Tanzania Agro-Holdings",
          location: "Kinondoni, Dar es Salaam",
          contact: "Rashid Kibwana (Managing Director)",
          pitch: "Habari Rashid! Niliona shughuli zenu za usambazaji wa mazao nchini. Sisi tunasaidia biashara za Kitanzania kuboresha mifumo yao ya usimamizi na usafirishaji ili kupunguza gharama za uendeshaji. Tungependa kushiriki ufumbuzi wetu na ninyi. Tunaweza kuongea kwa dakika 2 leo?"
        },
        {
          company: "Kahawa Cafe Group",
          location: "Kariakoo, Dar es Salaam",
          contact: "Amani Mwakalindile (Sourcing Head)",
          pitch: "Habari Amani! Niliona kuwa mnaongeza matawi mapya ya migahawa Kariakoo. Sisi tunatoa huduma za ugavi wa vyakula na vifaa vya migahawa kwa bei ya jumla. Ningependa kukutumia bei zetu za sasa tuone kama tunaweza kupunguza gharama zenu kwa 10%. Naweza kukutumia catalogue yetu?"
        },
        {
          company: "Swahili Tech Solutions",
          location: "Oysterbay, Dar es Salaam",
          contact: "Neema Shayo (HR Manager)",
          pitch: "Habari Neema, natumai siku yako inaenda vizuri. Sisi tunasaidia makampuni ya huduma Oysterbay kupata wateja wapya B2B kwa kutumia teknolojia ya kijani. Ningependa kuonyesha jinsi tunavyoweza kuongeza idadi ya wateja wenu kwa 30% ndani ya mwezi mmoja. Tunaweza kupanga simu fupi ya sekunde 30?"
        }
      ];
    }
  };

  const handleFinish = async () => {
    setIsFinishing(true);
    try {
      const words = description.toLowerCase().split(/\s+/);
      let detectedIndustry = 'general';
      if (words.some(w => ['ujenzi', 'construction', 'hardware', 'vifaa'].includes(w))) {
        detectedIndustry = 'construction';
      } else if (words.some(w => ['rembo', 'beauty', 'salon', 'saluni', 'vipodozi'].includes(w))) {
        detectedIndustry = 'retail';
      }

      await api.patch(
        '/api/v1/tenants/me',
        {
          industry_vertical: detectedIndustry,
          settings: {
            onboarding_complete: true,
            plain_description: description,
            default_locations: ['Dar es Salaam'],
            whatsapp_status: wa?.status || 'disconnected',
          },
        },
        token || undefined
      );

      toast('Setup complete! / Usanidi umekamilika', 'success');
      router.push('/dashboard');
    } catch (err) {
      toast('Failed to complete setup', 'error');
    } finally {
      setIsFinishing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 sm:px-6">
      
      {/* Top Header Progress */}
      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Setup Kijani AI</h1>
        <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">
          Hatua {step + 1} ya {STEPS.length} — {STEPS[step].titleEn}
        </p>
        
        {/* Progress Bar Dots */}
        <div className="flex gap-1.5 max-w-xs mx-auto pt-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                i <= step ? 'bg-emerald-600' : 'bg-slate-200 dark:bg-slate-800'
              }`}
            />
          ))}
        </div>
      </div>

      <Card className="mt-8 shadow-xl border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
        
        {/* STEP 1: WELCOME */}
        {step === 0 && (
          <div className="p-6 sm:p-8 space-y-6">
            <CardHeader className="p-0">
              <CardTitle className="text-xl sm:text-2xl text-emerald-700 dark:text-emerald-500 flex items-center gap-2">
                <Sparkles className="h-6 w-6 animate-pulse" />
                Karibu Kijani AI!
              </CardTitle>
              <CardDescription className="text-slate-500 dark:text-slate-400">
                Automated Swahili-English Sales Agents for Tanzanian B2B Businesses.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 text-slate-600 dark:text-slate-300 text-sm space-y-4 leading-relaxed">
              <p>
                Kijani AI deploys team of AI agents that automatically search Google Maps, BRELA registrations, and social profiles to discover businesses in Tanzania.
              </p>
              <p className="font-semibold text-slate-800 dark:text-white">
                Zero technical setups. Zero configuration.
              </p>
              <p>
                Just describe your business in plain Kiswahili or English, link your WhatsApp, and let our agents research leads, look up contacts, and draft custom messaging for you.
              </p>
            </CardContent>
            <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button onClick={() => setStep(1)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold flex items-center gap-2">
                Start Onboarding
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* STEP 2: DESCRIBE BUSINESS */}
        {step === 1 && (
          <div className="p-6 sm:p-8 space-y-6">
            <CardHeader className="p-0">
              <CardTitle className="text-xl text-slate-950 dark:text-white">
                Describe your business / Eleza biashara yako
              </CardTitle>
              <CardDescription className="text-slate-500 dark:text-slate-400">
                Write what you sell and who your target B2B customers are. Kiswahili and English are both supported.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 space-y-4">
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Example: Nnauza nondo, saruji na mabati ya ujenzi kwa makampuni ya kandarasi (contractors) yaliyopo Dar es Salaam na Dodoma..."
                rows={6}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 resize-none dark:text-white"
              />
              <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200/50 dark:border-slate-800/50 rounded-lg p-3.5 space-y-1.5 text-xs text-slate-500">
                <span className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">Suggested formats / Mifano ya kuandika:</span>
                <p>• &quot;I supply office stationery, printing papers, and toner cartridges to corporate offices in Dar es Salaam.&quot;</p>
                <p>• &quot;Ninasambaza vipodozi vya jumla na mafuta ya ngozi kwa saluni za kike na ma-spa mikoani.&quot;</p>
              </div>
            </CardContent>
            <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
              <Button 
                onClick={() => setStep(2)} 
                disabled={description.trim().length < 10}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
              >
                Analyze & Next
              </Button>
            </div>
          </div>
        )}

        {/* STEP 3: LINK WHATSAPP */}
        {step === 2 && (
          <div className="p-6 sm:p-8 space-y-6">
            <CardHeader className="p-0">
              <CardTitle className="text-xl text-slate-950 dark:text-white">
                Connect WhatsApp / Unganisha WhatsApp
              </CardTitle>
              <CardDescription className="text-slate-500 dark:text-slate-400">
                Kijani&apos;s Outreach Agent sends Swahili-English messages and voice notes through your linked WhatsApp number.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 space-y-4">
              <div className="flex flex-col items-center justify-center p-6 border border-slate-100 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-950/20 min-h-[240px]">
                {wa?.qr && wa?.status !== 'connected' && wa?.status !== 'offline' ? (
                  <div className="space-y-4 text-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={wa.qr} alt="WhatsApp QR" className="mx-auto h-44 w-44 border rounded-xl bg-white p-2 shadow-md animate-fade-in" />
                    <div className="space-y-1">
                      <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-500">Open WhatsApp → Linked Devices → Link a Device</p>
                      <p className="text-[10px] text-slate-400">QR code auto-refreshes every 10 seconds</p>
                    </div>
                  </div>
                ) : wa?.status === 'initializing' ? (
                  <div className="text-center space-y-3">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-emerald-600" />
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">Inapakia WhatsApp Web...</p>
                    <p className="text-xs text-slate-500 max-w-[280px]">Mchakato huu unachukua sekunde 15 hadi 30 (Takes 15-30 seconds)</p>
                  </div>
                ) : wa?.status === 'offline' ? (
                  <div className="text-center text-red-600 space-y-2 p-2">
                    <p className="text-sm font-semibold">WhatsApp Gateway Offline</p>
                    <p className="text-xs max-w-xs text-slate-500">Hakikisha huduma ya WhatsApp na Docker Desktop inafanya kazi.</p>
                  </div>
                ) : (
                  <div className="text-center text-slate-500 space-y-2">
                    <Loader2 className="mx-auto h-6 w-6 animate-spin text-slate-400" />
                    <p className="text-sm">Inatafuta msimbo wa QR... / Fetching QR...</p>
                  </div>
                )}
              </div>
              <p className="text-center text-xs text-slate-400">Unaweza kuruka hatua hii na kuunganisha baadae kwenye Mipangilio (You can skip and connect later in Settings)</p>
            </CardContent>
            <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
              <Button onClick={() => setStep(3)} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold">
                {wa?.status === 'connected' ? 'Next' : 'Link Later / Skip'}
              </Button>
            </div>
          </div>
        )}

        {/* STEP 4: AGENTS WORKING (SIMULATION) */}
        {step === 3 && (
          <div className="p-6 sm:p-8 space-y-6">
            <CardHeader className="p-0 text-center">
              <CardTitle className="text-xl text-slate-950 dark:text-white flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-emerald-600" />
                Agents at Work / Maajenti Wanaandaa Wateja
              </CardTitle>
              <CardDescription className="text-slate-500 dark:text-slate-400">
                Kijani AI agents are dynamically scouting and planning based on your business description...
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 space-y-6">
              {/* Progress Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span>Processing business insights</span>
                  <span>{agentProgress}%</span>
                </div>
                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-600 transition-all duration-500" style={{ width: `${agentProgress}%` }} />
                </div>
              </div>

              {/* Terminal Logs */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 space-y-2 min-h-[160px] max-h-[240px] overflow-y-auto shadow-inner">
                {agentLogs.length === 0 ? (
                  <p className="text-slate-600 animate-pulse">&gt; Inakagua mifumo ya maajenti...</p>
                ) : (
                  agentLogs.map((log, idx) => (
                    <p key={idx} className="animate-fade-in text-emerald-400">
                      <span className="text-slate-500">&gt;</span> {log}
                    </p>
                  ))
                )}
              </div>
            </CardContent>
          </div>
        )}

        {/* STEP 5: THE MAGIC MOMENT */}
        {step === 4 && (
          <div className="p-6 sm:p-8 space-y-6">
            <CardHeader className="p-0 text-center">
              <CardTitle className="text-2xl text-emerald-600 dark:text-emerald-500 flex items-center justify-center gap-2">
                <CheckCircle2 className="h-7 w-7 text-emerald-600" />
                Your First Leads Are Ready!
              </CardTitle>
              <CardDescription className="text-slate-500 dark:text-slate-400">
                Here are the first 3 Tanzanian leads discovered based on your description with pre-written Swahili/English WhatsApp pitches.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 space-y-6">
              
              {/* Lead Cards Carousels */}
              <div className="space-y-4 max-h-[380px] overflow-y-auto pr-1">
                {getLeads().map((lead, idx) => (
                  <div 
                    key={idx} 
                    className="p-5 border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/50 dark:bg-slate-900/40 relative shadow-sm space-y-3 hover:border-emerald-500/30 transition-all"
                  >
                    <div className="flex justify-between items-start">
                      <div className="space-y-0.5">
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">{lead.company}</h4>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {lead.location}</span>
                          <span className="flex items-center gap-1"><UserCheck className="h-3.5 w-3.5" /> {lead.contact}</span>
                        </div>
                      </div>
                      <span className="text-[10px] font-bold bg-emerald-600/10 text-emerald-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Ready
                      </span>
                    </div>

                    <div className="rounded-lg bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-800 p-3 text-xs text-slate-700 dark:text-slate-300 italic relative leading-relaxed shadow-inner">
                      <div className="absolute top-1 right-2 text-[10px] text-emerald-600 font-bold tracking-wider uppercase">WhatsApp Pitch</div>
                      &quot;{lead.pitch}&quot;
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            
            <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="outline" onClick={() => setStep(1)}>Back to edit</Button>
              <Button 
                onClick={handleFinish} 
                disabled={isFinishing}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold flex items-center gap-2"
              >
                {isFinishing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Launching...
                  </>
                ) : (
                  <>
                    Launch Outreach & Dashboard
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

      </Card>
    </div>
  );
}

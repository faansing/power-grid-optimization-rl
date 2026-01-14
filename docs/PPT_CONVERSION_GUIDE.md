# Converting Pitch Deck to PowerPoint

## Quick Guide

### Option 1: Use AI Tools (Recommended)
1. **Gamma.app** (https://gamma.app)
   - Upload `docs/PITCH_DECK.md`
   - Uses AI to auto-design slides
   - Professional templates included
   
2. **Beautiful.ai** (https://www.beautiful.ai)
   - Import markdown content
   - AI-powered design

### Option 2: Manual PowerPoint
1. Open PowerPoint/Keynote
2. For each "Slide X" section in PITCH_DECK.md:
   - Create new slide
   - Copy title and content
   - Add visuals/charts as suggested

### Option 3: Use ChatGPT/Claude
```
Prompt: "Convert this markdown pitch deck to PowerPoint format. 
Create speaker notes for each slide."

[Paste PITCH_DECK.md content]
```

## Slide Design Tips

### Slide 1-2: Hook (High Impact)
- Large numbers: "63%" in huge font
- Minimal text
- Professional dark theme

### Slide 5: Results Chart
Create bar chart:
- X-axis: AI (PPO), Traditional, Rule-Based
- Y-axis: Cost ($M)
- Values: 1.48, 4.02, 5.22
- Color AI bar green, others red/orange

### Slide 6: ROI Calculator
Visual formula:
```
1,000 MW × 8,760 h × $50/MWh = $438M/year
× 30% savings = $131M saved
```

### Slide 7: Market Size
Concentric circles:
- Center: $400M SAM
- Middle: $15B TAM
- Outer: Growth arrow 8.5% CAGR

### Slide 9: Competition Matrix
2×2 grid:
- X-axis: Speed (Slow → Fast)
- Y-axis: AI Capability (Low → High)
- Competitors in corners
- Us in top-right

## Color Scheme
- Primary: #10b981 (green - success)
- Secondary: #3b82f6 (blue - tech)
- Background: Dark (#0f172a → #1e293b gradient)
- Text: White/light gray
- Danger/Problem: #ef4444 (red)

## Fonts
- Headers: Inter Bold/Heavy
- Body: Inter Regular
- Numbers: Inter ExtraBold

## Key Visuals to Include

1. **Texas Blackout Image** (Slide 2)
   - News photo or infographic
   
2. **AI Learning Diagram** (Slide 4)
   ```
   [Data] → [Neural Network] → [Smart Decisions]
   ```

3. **Cost Comparison Chart** (Slide 5)
   - Already described above
   
4. **Market Growth Line** (Slide 7)
   - $15B to $25B by 2030
   
5. **Timeline Gantt Chart** (Slide 12)
   - 6 months: Beta
   - 12 months: Commercial
   - 18 months: Scale

## Animations (Optional)
- Slide 3: Bullet points appear one by one
- Slide 5: Bars grow from bottom
- Slide 6: Numbers count up
- Slide 12: Timeline reveals left to right

## Export Settings
- Format: PowerPoint (.pptx) or PDF
- Resolution: 1920×1080 (16:9)
- Embed fonts: Yes
- Save notes: Yes

## Quick Conversion Commands

### Using Pandoc (if installed)
```bash
pandoc docs/PITCH_DECK.md -o pitch_deck.pptx -t pptx
```

### Using Marp (Markdown Presentation)
```bash
npm install -g @marp-team/marp-cli
marp docs/PITCH_DECK.md --pptx -o pitch_deck.pptx
```

## Final Checks
- [ ] All 16 slides created
- [ ] Consistent color scheme
- [ ] Charts match data in evaluation_results.json
- [ ] Speaker notes added
- [ ] Proofread for typos
- [ ] Test presentation mode
- [ ] Export as PDF backup

## Time Estimate
- **AI Tool**: 15-30 minutes
- **Manual**: 2-3 hours
- **Hybrid**: 1 hour

**Recommended**: Use Gamma.app for fastest high-quality results.

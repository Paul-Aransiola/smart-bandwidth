# Responsive Design Breakpoints Guide

## Visual Breakpoint Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRA LARGE DESKTOP                          │
│                        1920px+                                  │
│  • Enhanced spacing and larger fonts                            │
│  • Maximum table width with all columns visible                 │
│  • 6-7 action buttons per device row                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  LARGE DESKTOP                           │
│                  1440px - 1919px                         │
│  • Standard desktop layout                               │
│  • All features fully visible                            │
│  • 5-6 action buttons per device row                     │
└──────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│              DESKTOP                           │
│              1200px - 1439px                   │
│  • Compact desktop layout                      │
│  • Filters in 3-column grid                    │
│  • 4-5 action buttons per device row           │
└────────────────────────────────────────────────┘

┌───────────────────────────────────────────┐
│         TABLET LANDSCAPE                  │
│         992px - 1199px                    │
│  • Header actions wrap                    │
│  • Filters in 2-column grid               │
│  • Horizontal table scrolling begins      │
│  • 3-4 action buttons per device row      │
└───────────────────────────────────────────┘

┌──────────────────────────────────┐
│      TABLET PORTRAIT             │
│      768px - 991px               │
│  • Header stacks vertically      │
│  • Filters stack (1 column)      │
│  • Bulk actions stack            │
│  • 2-3 action buttons per row    │
│  • Modals 95% width              │
└──────────────────────────────────┘

┌────────────────────────────┐
│   MOBILE LANDSCAPE         │
│   576px - 767px            │
│  • Full-width buttons      │
│  • Single column layout    │
│  • Horizontal scroll table │
│  • Stacked action buttons  │
│  • 98% width modals        │
└────────────────────────────┘

┌──────────────────────┐
│  MOBILE PORTRAIT     │
│  375px - 575px       │
│  • Full-screen UI    │
│  • Stack everything  │
│  • Min 44px touch    │
│  • Full-width modals │
│  • Reduced padding   │
└──────────────────────┘

┌────────────────┐
│ EXTRA SMALL    │
│ 320px - 374px  │
│  • Ultra-comp  │
│  • Minimal pad │
│  • Small fonts │
│  • Full-screen │
└────────────────┘
```

---

## Component Behavior by Screen Size

### Header Actions

**Desktop (1200px+)**

```
┌────────────────────────────────────────────────────────┐
│ [Bulk] [Scan] [Threshold] [Add] [CSV] [JSON]          │
└────────────────────────────────────────────────────────┘
```

**Tablet (768px - 991px)**

```
┌───────────────────────────┐
│ [Bulk Mode] [Scan Network]│
│ [Global] [Add] [CSV] [JSON]│
└───────────────────────────┘
```

**Mobile (< 768px)**

```
┌──────────────┐
│ [Bulk Mode]  │
│ [Scan]       │
│ [Threshold]  │
│ [Add Device] │
│ [Export CSV] │
│ [Export JSON]│
└──────────────┘
```

---

### Device Table

**Desktop View (1200px+)**

```
┌────────────────────────────────────────────────────────────────────────────┐
│ IP Address │ MAC │ Name │ Status │ Sent │ Recv │ Threshold │ Actions      │
├────────────────────────────────────────────────────────────────────────────┤
│ 192.168... │ aa: │ PC-1 │ Active │ 50MB │ 30MB │ 100 Mbps  │ [B][T][Th][H]│
└────────────────────────────────────────────────────────────────────────────┘
```

**Tablet View (768px - 991px)**

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Scroll →                                                      │
├─────────────────────────────────────────────────────────────────┤
│ IP │ MAC │ Name │ Status │ Sent │ Recv │ Threshold │ Actions  │
├─────────────────────────────────────────────────────────────────┤
│ 192│ aa: │ PC-1 │ Active │ 50MB │ 30MB │ 100 Mbps  │ [B][T]   │
└─────────────────────────────────────────────────────────────────┘
```

**Mobile View (< 768px)**

```
┌──────────────────────────────────────────────┐
│ ← Scroll Horizontally →                     │
├──────────────────────────────────────────────┤
│ IP │MAC│Name│Stat│Sent│Recv│Thr│ Actions  │
├──────────────────────────────────────────────┤
│ 192│aa:│PC-1│Act │50MB│30MB│100│ [Block]  │
│    │   │    │    │    │    │   │ [Throttle]│
└──────────────────────────────────────────────┘
```

---

### Modals

**Desktop Modal (1200px+)**

```
┌─────────────────────────────────────┐
│  Set Bandwidth Threshold        [X] │
├─────────────────────────────────────┤
│                                     │
│  Current Status:                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ │
│  │  Sent  │ │  Recv  │ │ Status │ │
│  │  50 MB │ │  30 MB │ │ Active │ │
│  └────────┘ └────────┘ └────────┘ │
│                                     │
│  Threshold: [100] Mbps              │
│  ☑ Auto-deactivate                  │
│  Time window: [5] minutes           │
│                                     │
│  [Save]  [Remove]  [Cancel]        │
└─────────────────────────────────────┘
```

**Tablet Modal (768px - 991px)**

```
┌──────────────────────────────┐
│  Threshold              [X]  │
├──────────────────────────────┤
│                              │
│  Status:                     │
│  ┌──────────────────────┐   │
│  │ Sent: 50 MB          │   │
│  ┌──────────────────────┐   │
│  │ Recv: 30 MB          │   │
│  ┌──────────────────────┐   │
│  │ Status: Active       │   │
│  └──────────────────────┘   │
│                              │
│  Threshold: [100] Mbps       │
│  ☑ Auto-deactivate           │
│  Time: [5] min               │
│                              │
│  [Save]                      │
│  [Remove]                    │
│  [Cancel]                    │
└──────────────────────────────┘
```

**Mobile Modal (< 768px)**

```
┌────────────────────────┐
│ Threshold         [X]  │
├────────────────────────┤
│ Status                 │
│ ┌────────────────────┐│
│ │ Sent: 50 MB        ││
│ └────────────────────┘│
│ ┌────────────────────┐│
│ │ Recv: 30 MB        ││
│ └────────────────────┘│
│ ┌────────────────────┐│
│ │ Status: Active     ││
│ └────────────────────┘│
│                        │
│ Threshold              │
│ [100] Mbps             │
│                        │
│ ☑ Auto-deactivate      │
│                        │
│ Time window            │
│ [5] minutes            │
│                        │
│ [     Save      ]      │
│ [   Remove      ]      │
│ [   Cancel      ]      │
│                        │
│ (Full Screen)          │
└────────────────────────┘
```

---

## Touch Target Sizes

### Minimum Touch Targets (Mobile)

- **Buttons**: 44px × 44px
- **Checkboxes**: 44px × 44px (including padding)
- **Table cells (clickable)**: 44px height minimum
- **Close button**: 44px × 44px
- **Filter inputs**: 44px height

### Desktop Click Targets

- **Buttons**: 32px × auto
- **Checkboxes**: 18px × 18px
- **Table cells**: Auto height
- **Close button**: 32px × 32px

---

## Font Size Progression

```
Device Type       | Heading (h2) | Body Text | Small Text
------------------|--------------|-----------|------------
Extra Large       | 2.5rem (40px)| 1rem      | 0.875rem
Desktop           | 2rem (32px)  | 1rem      | 0.875rem
Tablet            | 1.5rem (24px)| 0.9rem    | 0.85rem
Mobile Landscape  | 1.25rem (20px)| 0.875rem | 0.8rem
Mobile Portrait   | 1.1rem (18px)| 0.8rem    | 0.75rem
Extra Small       | 1rem (16px)  | 0.75rem   | 0.7rem
```

---

## Spacing Scale

```
Screen Size       | Container | Section  | Element
------------------|-----------|----------|----------
Desktop (1200px+) | 2rem      | 1.5rem   | 1rem
Tablet (768px+)   | 1.5rem    | 1.25rem  | 0.75rem
Mobile (576px+)   | 1rem      | 1rem     | 0.5rem
Small Mobile      | 0.5rem    | 0.75rem  | 0.35rem
```

---

## Grid Behavior

### Filters Bar

- **Desktop (1200px+)**: 4 columns
- **Tablet Landscape (992px)**: 3 columns
- **Tablet Portrait (768px)**: 2 columns
- **Mobile (< 768px)**: 1 column

### Status Grid (Modal)

- **Desktop (1200px+)**: 3 columns
- **Tablet (768px+)**: 2 columns
- **Mobile (< 768px)**: 1 column

### Bulk Action Buttons

- **Desktop (992px+)**: Horizontal row
- **Tablet (768px)**: 2 columns
- **Mobile (< 768px)**: 1 column (stacked)

---

## Testing Devices

### iOS Devices

```
iPhone SE      : 375 × 667  (Mobile Portrait)
iPhone 12/13   : 390 × 844  (Mobile Portrait)
iPhone 12/13 Pro Max: 428 × 926 (Mobile Portrait)
iPad Mini      : 768 × 1024 (Tablet Portrait)
iPad Pro 11"   : 834 × 1194 (Tablet Portrait)
iPad Pro 12.9" : 1024 × 1366 (Tablet Landscape)
```

### Android Devices

```
Galaxy S21     : 360 × 800  (Mobile Portrait)
Galaxy S21+    : 384 × 854  (Mobile Portrait)
Pixel 5        : 393 × 851  (Mobile Portrait)
Galaxy Tab S7  : 753 × 1037 (Tablet Portrait)
```

### Desktop

```
Laptop         : 1366 × 768 (Desktop)
Desktop HD     : 1920 × 1080 (Large Desktop)
Desktop 2K     : 2560 × 1440 (Extra Large)
Desktop 4K     : 3840 × 2160 (Extra Large)
```

---

## Browser Testing Matrix

| Browser | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Chrome  | ✅      | ✅     | ✅     |
| Firefox | ✅      | ✅     | ✅     |
| Safari  | ✅      | ✅     | ✅     |
| Edge    | ✅      | ✅     | ✅     |
| Samsung Internet | - | -  | ✅     |

---

## Performance Benchmarks

### Target Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Mobile Specific

- **Touch Response**: < 50ms
- **Scroll FPS**: 60fps
- **Animation FPS**: 60fps
- **Bundle Size**: < 500KB (gzipped)

---

## Accessibility Checklist

- [x] Touch targets minimum 44×44px
- [x] Text readable at 200% zoom
- [x] Color contrast ratio > 4.5:1
- [x] Keyboard navigation works
- [x] Focus indicators visible
- [x] Screen reader friendly
- [x] No horizontal scroll (except tables)
- [x] Portrait and landscape support

---

## Quick Test Commands

### Test on Local Network Devices

```bash
# Start with network access
cd dashboard-react && npm run dev -- --host

# Access from mobile device
# http://YOUR_IP:5173
```

### Browser DevTools Testing

```
Chrome DevTools:
1. Press F12
2. Click device toolbar (Ctrl+Shift+M)
3. Select device from dropdown
4. Test all breakpoints

Responsive sizes to test:
- 320px (iPhone SE)
- 375px (iPhone 12)
- 414px (iPhone 12 Pro Max)
- 768px (iPad)
- 1024px (iPad Pro)
- 1440px (Laptop)
- 1920px (Desktop)
```

---

## Common Issues & Solutions

### Issue: Table overflows on mobile

**Solution**: Already implemented - table wrapper with horizontal scroll

### Issue: Buttons too small on mobile

**Solution**: Already implemented - full-width buttons below 768px

### Issue: Modal too large on mobile

**Solution**: Already implemented - full-screen modals below 480px

### Issue: Text unreadable on small screens

**Solution**: Already implemented - progressive font size reduction

### Issue: Touch targets too small

**Solution**: Already implemented - minimum 44×44px on touch devices

---

## Next Steps for Perfect Responsiveness

1. **Add Viewport Meta Tag** (if not present):

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

2. **Test on Real Devices**: Use BrowserStack or physical devices

3. **Monitor Performance**: Use Lighthouse for mobile performance scores

4. **Add Loading States**: Skeleton screens for better perceived performance

5. **Optimize Images**: Use responsive images with `srcset`

6. **Consider PWA**: Add manifest.json for installable app experience
